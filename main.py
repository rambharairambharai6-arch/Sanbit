import os
import secrets
import sqlite3
import asyncio
import threading
from urllib.parse import urlparse

from flask import Flask, redirect
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
    raise RuntimeError(
        "BOT_TOKEN is missing. Add BOT_TOKEN in Railway Variables."
    )


# =========================================================
# FLASK WEB APP
# IMPORTANT: Railway will run "main:web"
# =========================================================

web = Flask(__name__)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
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
    conn = get_db()

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
# URL VALIDATION
# =========================================================

def is_valid_url(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.netloc:
            return False

        if " " in url:
            return False

        if len(url) > 4096:
            return False

        return True

    except Exception:
        return False


# =========================================================
# SHORT CODE
# =========================================================

def generate_code(length=7):
    characters = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
    )

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )


def create_short_link(user_id, original_url):
    conn = get_db()

    try:
        while True:
            code = generate_code()

            existing = conn.execute(
                """
                SELECT id
                FROM links
                WHERE short_code = ?
                """,
                (code,)
            ).fetchone()

            if not existing:
                break

        conn.execute(
            """
            INSERT INTO links (
                telegram_id,
                original_url,
                short_code
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                original_url,
                code
            )
        )

        conn.commit()

        return code

    finally:
        conn.close()


# =========================================================
# TELEGRAM MENU
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
                callback_data="id"
            ),
            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# /START
# =========================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    save_user(user)

    context.user_data["waiting_for_url"] = False

    text = (
        "👋 Welcome to IK-O Shortener!\n\n"
        "🔗 Create short links quickly and easily.\n\n"
        "💰 Price: FREE\n"
        "👥 Channel membership: Not required\n"
        "✅ Approval: Not required\n\n"
        "Press the button below to begin."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


# =========================================================
# /ID
# =========================================================

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    save_user(user)

    await update.message.reply_text(
        "🆔 Your Telegram ID:\n\n"
        f"{user.id}",
        reply_markup=main_menu()
    )


# =========================================================
# BUTTONS
# =========================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    save_user(user)

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------

    if query.data == "create":

        context.user_data["waiting_for_url"] = True

        await query.message.reply_text(
            "🔗 Send the URL you want to shorten.\n\n"
            "Example:\n"
            "https://example.com"
        )

        return

    # -----------------------------------------------------
    # ID
    # -----------------------------------------------------

    if query.data == "id":

        await query.message.reply_text(
            "🆔 Your Telegram ID:\n\n"
            f"{user.id}",
            reply_markup=main_menu()
        )

        return

    # -----------------------------------------------------
    # HELP
    # -----------------------------------------------------

    if query.data == "help":

        context.user_data["waiting_for_url"] = False

        await query.message.reply_text(
            "ℹ️ IK-O Shortener Help\n\n"
            "🔗 Create Short Link\n"
            "Send any valid HTTP/HTTPS URL.\n\n"
            "📊 My Statistics\n"
            "See your total links and clicks.\n\n"
            "📋 My Links\n"
            "See your recently created links.\n\n"
            "🆔 My ID\n"
            "Show your Telegram ID.\n\n"
            "💰 This bot is completely FREE.",
            reply_markup=main_menu()
        )

        return

    # -----------------------------------------------------
    # STATS
    # -----------------------------------------------------

    if query.data == "stats":

        conn = get_db()

        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_links,
                COALESCE(SUM(clicks), 0) AS total_clicks
            FROM links
            WHERE telegram_id = ?
            """,
            (user.id,)
        ).fetchone()

        conn.close()

        await query.message.reply_text(
            "📊 Your Statistics\n\n"
            f"🔗 Total Links: {row['total_links']}\n"
            f"👆 Total Clicks: {row['total_clicks']}",
            reply_markup=main_menu()
        )

        return

    # -----------------------------------------------------
    # LINKS
    # -----------------------------------------------------

    if query.data == "links":

        conn = get_db()

        rows = conn.execute(
            """
            SELECT
                short_code,
                original_url,
                clicks
            FROM links
            WHERE telegram_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (user.id,)
        ).fetchall()

        conn.close()

        if not rows:

            await query.message.reply_text(
                "📋 You haven't created any links yet.",
                reply_markup=main_menu()
            )

            return

        message = "📋 Your Latest Links\n\n"

        for row in rows:

            short_url = (
                f"{SHORT_DOMAIN}/{row['short_code']}"
            )

            message += (
                f"🔗 {short_url}\n"
                f"👆 Clicks: {row['clicks']}\n\n"
            )

        await query.message.reply_text(
            message,
            reply_markup=main_menu()
        )

        return


# =========================================================
# URL HANDLER
# =========================================================

async def url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    save_user(user)

    if not context.user_data.get("waiting_for_url", False):

        await update.message.reply_text(
            "Please press 🔗 Create Short Link first.",
            reply_markup=main_menu()
        )

        return

    url = (update.message.text or "").strip()

    if not is_valid_url(url):

        await update.message.reply_text(
            "❌ Invalid URL.\n\n"
            "Please send a complete URL beginning with:\n\n"
            "https://example.com"
        )

        return

    try:

        code = create_short_link(
            user.id,
            url
        )

        short_url = (
            f"{SHORT_DOMAIN}/{code}"
        )

        context.user_data["waiting_for_url"] = False

        await update.message.reply_text(
            "✅ Short link created!\n\n"
            f"🔗 {short_url}\n\n"
            "Your link is ready.",
            reply_markup=main_menu()
        )

    except Exception as error:

        print(
            "SHORT LINK ERROR:",
            repr(error)
        )

        await update.message.reply_text(
            "❌ Unable to create the short link right now.\n"
            "Please try again.",
            reply_markup=main_menu()
        )


# =========================================================
# WEBSITE HOME
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
    margin:0;
    background:#f4f6f8;
    font-family:Arial,sans-serif;
">

<div style="
    max-width:600px;
    margin:80px auto;
    background:white;
    padding:40px;
    border-radius:16px;
    text-align:center;
    box-shadow:0 4px 20px rgba(0,0,0,.08);
">

    <h1>🔗 IK-O Shortener</h1>

    <p>
        Free URL shortener.
    </p>

    <p>
        Create short links quickly and easily.
    </p>

</div>

</body>
</html>
"""


# =========================================================
# SHORT LINK REDIRECT
# =========================================================

@web.route("/<short_code>")
def redirect_short_link(short_code):

    # Ignore common browser request
    if short_code == "favicon.ico":
        return "Not Found", 404

    conn = get_db()

    row = conn.execute(
        """
        SELECT original_url
        FROM links
        WHERE short_code = ?
        """,
        (short_code,)
    ).fetchone()

    if not row:

        conn.close()

        return """
        <h2>404 - Short Link Not Found</h2>
        """, 404

    conn.execute(
        """
        UPDATE links
        SET clicks = clicks + 1
        WHERE short_code = ?
        """,
        (short_code,)
    )

    conn.commit()
    conn.close()

    return redirect(
        row["original_url"],
        code=302
    )


# =========================================================
# TELEGRAM BOT THREAD
# =========================================================

def run_telegram_bot():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "id",
            id_command
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            url_handler
        )
    )

    print("================================")
    print("IK-O SHORTENER BOT")
    print("Bot is starting...")
    print("Domain:", SHORT_DOMAIN)
    print("================================")

    loop.run_until_complete(
        application.initialize()
    )

    loop.run_until_complete(
        application.start()
    )

    loop.run_until_complete(
        application.updater.start_polling(
            drop_pending_updates=True
        )
    )

    print("BOT IS RUNNING SUCCESSFULLY")

    try:

        loop.run_forever()

    except KeyboardInterrupt:

        pass

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

        loop.close()


# =========================================================
# INITIALIZE
# =========================================================

init_database()

threading.Thread(
    target=run_telegram_bot,
    daemon=True
).start()


# =========================================================
# LOCAL RUN
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "8080")
    )

    web.run(
        host="0.0.0.0",
        port=port
    )