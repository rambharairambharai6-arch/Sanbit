import os
import secrets
import sqlite3
from urllib.parse import urlparse

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Fixed short-link domain
SHORT_DOMAIN = "https://ik-o.site"

# Public channel used for membership requirement
REQUIRED_CHANNEL = "@joy_igcc"

# Your Telegram ID
OWNER_ID = 7774294727

DATABASE = "shortlinks.db"
CODE_LENGTH = 7


# ============================================================
# DATABASE
# ============================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            approved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def register_user(user):
    connection = get_db()

    connection.execute("""
        INSERT INTO users (telegram_id, username)
        VALUES (?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET username = excluded.username
    """, (
        user.id,
        user.username
    ))

    connection.commit()
    connection.close()


def is_approved(user_id):
    connection = get_db()

    row = connection.execute(
        "SELECT approved FROM users WHERE telegram_id = ?",
        (user_id,)
    ).fetchone()

    connection.close()

    return bool(row and row["approved"] == 1)


def set_approved(user_id, approved=True):
    connection = get_db()

    connection.execute("""
        INSERT INTO users (telegram_id, approved)
        VALUES (?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET approved = excluded.approved
    """, (
        user_id,
        1 if approved else 0
    ))

    connection.commit()
    connection.close()


# ============================================================
# URL VALIDATION
# ============================================================

def valid_url(url):
    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
            and " " not in url
        )

    except Exception:
        return False


# ============================================================
# SHORT CODE
# ============================================================

def generate_code():
    alphabet = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
    )

    return "".join(
        secrets.choice(alphabet)
        for _ in range(CODE_LENGTH)
    )


def create_short_link(user_id, original_url):
    connection = get_db()

    while True:
        code = generate_code()

        exists = connection.execute(
            "SELECT id FROM links WHERE short_code = ?",
            (code,)
        ).fetchone()

        if not exists:
            break

    connection.execute("""
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

    connection.commit()
    connection.close()

    return f"{SHORT_DOMAIN}/{code}"


# ============================================================
# CHANNEL CHECK
# ============================================================

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL,
            user_id=user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as error:
        print("Channel membership check error:", error)
        return False


# ============================================================
# MENU
# ============================================================

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
                "📢 Join Channel",
                url="https://t.me/joy_igcc"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Check Membership",
                callback_data="check"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# START
# ============================================================

async def start(update, context):
    user = update.effective_user

    register_user(user)

    await update.message.reply_text(
        "👋 Welcome to IK-O Shortener!\n\n"
        "To create short links you must:\n\n"
        "1️⃣ Join our required channel\n"
        "2️⃣ DM the bot owner for approval\n"
        "3️⃣ After approval, create your short link\n\n"
        "Use the menu below.",
        reply_markup=main_menu()
    )


# ============================================================
# BUTTON HANDLER
# ============================================================

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    register_user(user)

    # ---------------- CHECK MEMBERSHIP ----------------

    if query.data == "check":

        joined = await check_membership(
            user.id,
            context
        )

        if joined:
            await query.message.reply_text(
                "✅ Channel membership verified.\n\n"
                "Now DM the owner for approval before "
                "creating a short link."
            )
        else:
            await query.message.reply_text(
                "❌ You haven't joined the required channel yet.\n\n"
                "Join here:\n"
                "https://t.me/joy_igcc\n\n"
                "Then press 'Check Membership' again."
            )

        return

    # ---------------- CREATE ----------------

    if query.data == "create":

        joined = await check_membership(
            user.id,
            context
        )

        if not joined:
            await query.message.reply_text(
                "❌ Channel membership required.\n\n"
                "Please join:\n"
                "https://t.me/joy_igcc\n\n"
                "Then check your membership."
            )
            return

        if not is_approved(user.id):
            await query.message.reply_text(
                "⏳ Approval required.\n\n"
                "Please DM the owner "
                f"@JOYxWEB and request approval.\n\n"
                "Your Telegram ID:\n"
                f"`{user.id}`",
                parse_mode="Markdown"
            )
            return

        context.user_data["waiting_for_url"] = True

        await query.message.reply_text(
            "🔗 Send the URL you want to shorten.\n\n"
            "Example:\n"
            "https://example.com"
        )

        return

    # ---------------- STATS ----------------

    if query.data == "stats":

        connection = get_db()

        row = connection.execute("""
            SELECT
                COUNT(*) AS total_links,
                COALESCE(SUM(clicks), 0) AS total_clicks
            FROM links
            WHERE telegram_id = ?
        """, (user.id,)).fetchone()

        connection.close()

        await query.message.reply_text(
            "📊 Your Statistics\n\n"
            f"🔗 Links: {row['total_links']}\n"
            f"👆 Clicks: {row['total_clicks']}"
        )

        return

    # ---------------- LINKS ----------------

    if query.data == "links":

        connection = get_db()

        rows = connection.execute("""
            SELECT short_code, original_url, clicks
            FROM links
            WHERE telegram_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (user.id,)).fetchall()

        connection.close()

        if not rows:
            await query.message.reply_text(
                "📭 You haven't created any links yet."
            )
            return

        output = ["📋 Your recent links:\n"]

        for row in rows:
            output.append(
                f"🔗 {SHORT_DOMAIN}/{row['short_code']}\n"
                f"👆 Clicks: {row['clicks']}\n"
                f"🌐 {row['original_url'][:80]}\n"
            )

        await query.message.reply_text(
            "\n".join(output)
        )


# ============================================================
# URL MESSAGE
# ============================================================

async def handle_message(update, context):

    user = update.effective_user
    register_user(user)

    # Only process URL when user clicked Create
    if not context.user_data.get("waiting_for_url"):
        await update.message.reply_text(
            "Please use /start and select an option.",
            reply_markup=main_menu()
        )
        return

    # Check channel again
    joined = await check_membership(
        user.id,
        context
    )

    if not joined:
        context.user_data["waiting_for_url"] = False

        await update.message.reply_text(
            "❌ You must join the required channel first."
        )
        return

    # Check owner approval
    if not is_approved(user.id):
        context.user_data["waiting_for_url"] = False

        await update.message.reply_text(
            "⏳ Your account is not approved yet.\n\n"
            f"Please DM @JOYxWEB for approval."
        )
        return

    url = (update.message.text or "").strip()

    if not valid_url(url):
        await update.message.reply_text(
            "❌ Invalid URL.\n\n"
            "Please send a valid URL beginning with "
            "http:// or https://"
        )
        return

    short_url = create_short_link(
        user.id,
        url
    )

    context.user_data["waiting_for_url"] = False

    await update.message.reply_text(
        "✅ Short link created successfully!\n\n"
        f"🔗 {short_url}\n\n"
        "Original URL:\n"
        f"{url}",
        reply_markup=main_menu()
    )


# ============================================================
# OWNER APPROVAL COMMAND
# ============================================================

async def approve(update, context):

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/approve USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid Telegram ID."
        )
        return

    set_approved(user_id, True)

    await update.message.reply_text(
        "✅ User approved successfully.\n\n"
        f"Telegram ID: {user_id}"
    )


# ============================================================
# OWNER REVOKE
# ============================================================

async def revoke(update, context):

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/revoke USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid Telegram ID."
        )
        return

    set_approved(user_id, False)

    await update.message.reply_text(
        "🚫 User approval revoked.\n\n"
        f"Telegram ID: {user_id}"
    )


# ============================================================
# ERROR
# ============================================================

async def error_handler(update, context):
    print(
        "Telegram error:",
        repr(context.error)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    init_database()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("approve", approve)
    )

    application.add_handler(
        CommandHandler("revoke", revoke)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    application.add_error_handler(error_handler)

    print("IK-O Shortener Bot started successfully.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()