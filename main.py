import os
import secrets
import sqlite3
import threading
from urllib.parse import urlparse

from flask import Flask, redirect, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

SHORT_DOMAIN = "https://ik-o.site"
DATABASE = os.getenv("DATABASE", "shortlinks.db")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")


# =========================================================
# FLASK APP
# =========================================================

web = Flask(__name__)


# =========================================================
# DATABASE
# =========================================================

def db():
    conn = sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# USER
# =========================================================

def save_user(user):
    conn = db()

    conn.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            first_name
        )
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (
        user.id,
        user.username or "",
        user.first_name or ""
    ))

    conn.commit()
    conn.close()


# =========================================================
# URL CHECK
# =========================================================

def valid_url(url):
    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
            and len(url) <= 2048
        )

    except Exception:
        return False


# =========================================================
# SHORT CODE
# =========================================================

def generate_code():
    alphabet = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
    )

    return "".join(
        secrets.choice(alphabet)
        for _ in range(7)
    )


def create_short_link(user_id, original_url):

    conn = db()

    while True:
        code = generate_code()

        exists = conn.execute(
            "SELECT 1 FROM links WHERE short_code = ?",
            (code,)
        ).fetchone()

        if not exists:
            break

    conn.execute("""
        INSERT INTO links (
            telegram_id,
            original_url,
            short_code
        )
        VALUES (?, ?, ?)
    """, (
        user_id,
        original_url,
        code
    ))

    conn.commit()
    conn.close()

    return code


# =========================================================
# MENU
# =========================================================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "🔗 Create Short Link",
                callback_data="create"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 My Statistics",
                callback_data="stats"
            ),
            InlineKeyboardButton(
                "📋 My Links",
                callback_data="links"
            )
        ],
        [
            InlineKeyboardButton(
                "🆔 My ID",
                callback_data="myid"
            ),
            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    context.user_data["waiting_url"] = False

    await update.message.reply_text(
        "👋 Welcome to IK-O Shortener!\n\n"
        "🔗 Create short links completely FREE.\n\n"
        "Just press 'Create Short Link' and send "
        "your URL.\n\n"
        "No payment, channel membership or approval "
        "is required.",
        reply_markup=main_menu()
    )


# =========================================================
# ID COMMAND
# =========================================================

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    await update.message.reply_text(
        "🆔 Your Telegram ID:\n\n"
        f"`{update.effective_user.id}`",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user
    save_user(user)

    if query.data == "create":

        context.user_data["waiting_url"] = True

        await query.message.reply_text(
            "🔗 Send the URL you want to shorten.\n\n"
            "Example:\n"
            "https://example.com"
        )

    elif query.data == "myid":

        await query.message.reply_text(
            "🆔 Your Telegram ID:\n\n"
            f"`{user.id}`",
            parse_mode="Markdown"
        )

    elif query.data == "help":

        context.user_data["waiting_url"] = False

        await query.message.reply_text(
            "ℹ️ How to use\n\n"
            "1️⃣ Press 🔗 Create Short Link\n"
            "2️⃣ Send a valid http/https URL\n"
            "3️⃣ Your short link is generated instantly\n\n"
            "💰 Cost: FREE\n"
            "👥 Membership: Not required\n"
            "✅ Manual approval: Not required",
            reply_markup=main_menu()
        )

    elif query.data == "stats":

        conn = db()

        row = conn.execute("""
            SELECT
                COUNT(*) AS total_links,
                COALESCE(SUM(clicks), 0) AS total_clicks
            FROM links
            WHERE telegram_id = ?
        """, (user.id,)).fetchone()

        conn.close()

        await query.message.reply_text(
            "📊 Your Statistics\n\n"
            f"🔗 Total Links: {row['total_links']}\n"
            f"👆 Total Clicks: {row['total_clicks']}",
            reply_markup=main_menu()
        )

    elif query.data == "links":

        conn = db()

        rows = conn.execute("""
            SELECT short_code, original_url, clicks
            FROM links
            WHERE telegram_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (user.id,)).fetchall()

        conn.close()

        if not rows:
            await query.message.reply_text(
                "📋 You haven't created any links yet.",
                reply_markup=main_menu()
            )
            return

        text = "📋 Your Latest Links\n\n"

        for row in rows:

            short_url = (
                f"{SHORT_DOMAIN}/{row['short_code']}"
            )

            text += (
                f"🔗 {short_url}\n"
                f"👆 Clicks: {row['clicks']}\n\n"
            )

        await query.message.reply_text(
            text,
            reply_markup=main_menu()
        )


# =========================================================
# URL MESSAGE
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    save_user(update.effective_user)

    if not context.user_data.get("waiting_url"):

        await update.message.reply_text(
            "Please press 🔗 Create Short Link first.",
            reply_markup=main_menu()
        )

        return

    url = (update.message.text or "").strip()

    if not valid_url(url):

        await update.message.reply_text(
            "❌ Invalid URL.\n\n"
            "Please send a valid URL starting with:\n"
            "http:// or https://"
        )

        return

    user_id = update.effective_user.id

    try:

        code = create_short_link(
            user_id,
            url
        )

        short_url = (
            f"{SHORT_DOMAIN}/{code}"
        )

        context.user_data["waiting_url"] = False

        await update.message.reply_text(
            "✅ Short link created successfully!\n\n"
            f"🔗 {short_url}\n\n"
            "👆 Tap the link to open it.",
            reply_markup=main_menu()
        )

    except Exception as error:

        print(
            "SHORT LINK ERROR:",
            repr(error)
        )

        await update.message.reply_text(
            "❌ Something went wrong while creating "
            "the short link. Please try again."
        )


# =========================================================
# WEB HOME
# =========================================================

@web.route("/")
def home():

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IK-O Shortener</title>
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
    </head>

    <body style="
        font-family:Arial;
        text-align:center;
        padding:60px;
        background:#f5f7fa;
    ">

        <h1>IK-O Shortener</h1>

        <p>
            Free URL shortener.
        </p>

        <p>
            Create short links quickly and easily.
        </p>

    </body>
    </html>
    """


# =========================================================
# REDIRECT
# =========================================================

@web.route("/<short_code>")
def redirect_link(short_code):

    conn = db()

    row = conn.execute("""
        SELECT original_url
        FROM links
        WHERE short_code = ?
    """, (short_code,)).fetchone()

    if not row:

        conn.close()

        return jsonify({
            "error": "Short link not found"
        }), 404

    conn.execute("""
        UPDATE links
        SET clicks = clicks + 1
        WHERE short_code = ?
    """, (short_code,))

    conn.commit()
    conn.close()

    return redirect(
        row["original_url"],
        code=302
    )


# =========================================================
# RUN TELEGRAM BOT
# =========================================================

def run_bot():

    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("id", my_id)
    )

    application.add_handler(
        CallbackQueryHandler(buttons)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("IK-O Shortener Bot starting...")

    loop.run_until_complete(
        application.initialize()
    )

    loop.run_until_complete(
        application.start()
    )

    loop.run_until_complete(
        application.updater.start_polling()
    )

    print("IK-O Shortener Bot is running.")

    try:
        loop.run_forever()

    finally:

        loop.run_until_complete(
            application.updater.stop()
        )

        loop.run_until_complete(
            application.stop()
        )

        loop.run_until_complete(
            application.shutdown()
        )


# =========================================================
# START
# =========================================================

init_db()

bot_thread = threading.Thread(
    target=run_bot,
    daemon=True
)

bot_thread.start()


if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "8080")
    )

    web.run(
        host="0.0.0.0",
        port=port
    )