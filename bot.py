import os
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CopyTextButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_USERNAME = "@JOYxWEB"
CHANNEL_USERNAME = "@joy_web"
CHANNEL_URL = "https://t.me/joy_web"

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    name = user.first_name if user else "User"

    text = (
        "╔════════════════════════════╗\n"
        "        ✦ 𝐉𝐎𝐘 𝐖𝐄𝐁 𝐁𝐎𝐓 ✦\n"
        "╚════════════════════════════╝\n\n"

        f"👋 Welcome, {name}!\n\n"

        "🔥 Welcome to the official JOY WEB Bot.\n"
        "⚡ Fast • Simple • Secure\n"
        "💎 Premium Style Bot\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 𝐁𝐎𝐓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🆔 /id\n"
        "➜ Apni Chat ID dekhein\n\n"

        "ℹ️ /info\n"
        "➜ Bot ki information\n\n"

        "🆘 /help\n"
        "➜ Help & commands\n\n"

        "👑 /owner\n"
        "➜ Owner information\n\n"

        "📢 /channel\n"
        "➜ Official channel\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 𝐉𝐎𝐘 𝐖𝐄𝐁 • 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🆔 MY ID",
                callback_data="my_id"
            ),
            InlineKeyboardButton(
                "ℹ️ INFO",
                callback_data="info"
            ),
        ],
        [
            InlineKeyboardButton(
                "🆘 HELP",
                callback_data="help"
            ),
            InlineKeyboardButton(
                "👑 OWNER",
                url="https://t.me/JOYxWEB"
            ),
        ],
        [
            InlineKeyboardButton(
                "📢 OFFICIAL CHANNEL",
                url=CHANNEL_URL
            )
        ],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# ID COMMAND
# =========================================================

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not chat:
        return

    chat_id = str(chat.id)

    user_name = user.first_name if user else "Unknown"

    text = (
        "╔════════════════════════════╗\n"
        "          🆔 𝐘𝐎𝐔𝐑 𝐈𝐃\n"
        "╚════════════════════════════╝\n\n"

        f"👤 Name: {user_name}\n"
        f"💬 Chat Type: {chat.type}\n\n"

        "🆔 Your Chat ID:\n"
        f"`{chat_id}`\n\n"

        "👇 Neeche button dabakar ID copy karein."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📋 COPY CHAT ID",
                copy_text=CopyTextButton(text=chat_id)
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 BACK TO MENU",
                callback_data="home"
            )
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# INFO COMMAND
# =========================================================

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔════════════════════════════╗\n"
        "          ℹ️ 𝐁𝐎𝐓 𝐈𝐍𝐅𝐎\n"
        "╚════════════════════════════╝\n\n"

        "🤖 Bot: JOY WEB BOT\n"
        "⚡ Status: Online\n"
        "🔐 Security: Enabled\n"
        "🚀 Version: 1.0\n\n"

        "👑 Owner: @JOYxWEB\n"
        "📢 Channel: @joy_web\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 Thanks for using JOY WEB BOT\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 CHANNEL",
                url=CHANNEL_URL
            ),
            InlineKeyboardButton(
                "👑 OWNER",
                url="https://t.me/JOYxWEB"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 HOME",
                callback_data="home"
            )
        ],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# HELP COMMAND
# =========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔════════════════════════════╗\n"
        "           🆘 𝐇𝐄𝐋𝐏\n"
        "╚════════════════════════════╝\n\n"

        "📚 Available Commands:\n\n"

        "🟢 /start\n"
        "➜ Main menu open karein\n\n"

        "🆔 /id\n"
        "➜ Apni Chat ID dekhein\n\n"

        "ℹ️ /info\n"
        "➜ Bot information\n\n"

        "🆘 /help\n"
        "➜ Help menu\n\n"

        "👑 /owner\n"
        "➜ Owner information\n\n"

        "📢 /channel\n"
        "➜ Official channel\n"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🏠 HOME",
                callback_data="home"
            )
        ]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# OWNER COMMAND
# =========================================================

async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔════════════════════════════╗\n"
        "          👑 𝐎𝐖𝐍𝐄𝐑\n"
        "╚════════════════════════════╝\n\n"

        "👑 Owner: @JOYxWEB\n\n"
        "For official updates and support,\n"
        "please use the official channel."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👑 CONTACT OWNER",
                url="https://t.me/JOYxWEB"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 OFFICIAL CHANNEL",
                url=CHANNEL_URL
            )
        ],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# CHANNEL COMMAND
# =========================================================

async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔════════════════════════════╗\n"
        "          📢 𝐂𝐇𝐀𝐍𝐍𝐄𝐋\n"
        "╚════════════════════════════╝\n\n"

        "🔥 Join our official channel.\n\n"
        "📢 @joy_web"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 JOIN CHANNEL",
                url=CHANNEL_URL
            )
        ]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# BUTTON CALLBACKS
# =========================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user = query.from_user
    chat = query.message.chat

    if query.data == "my_id":
        chat_id = str(chat.id)

        text = (
            "🆔 𝐘𝐎𝐔𝐑 𝐂𝐇𝐀𝐓 𝐈𝐃\n\n"
            f"👤 Name: {user.first_name}\n"
            f"💬 Type: {chat.type}\n\n"
            f"ID: `{chat_id}`\n\n"
            "👇 Copy karne ke liye button press karein."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 COPY ID",
                    copy_text=CopyTextButton(text=chat_id)
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 HOME",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "info":
        text = (
            "ℹ️ 𝐉𝐎𝐘 𝐖𝐄𝐁 𝐁𝐎𝐓\n\n"
            "🤖 Status: Online\n"
            "⚡ Fast & Simple\n"
            "🔐 Secure bot structure\n\n"
            "👑 Owner: @JOYxWEB\n"
            "📢 Channel: @joy_web"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 CHANNEL",
                    url=CHANNEL_URL
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 HOME",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "help":
        text = (
            "🆘 𝐇𝐄𝐋𝐏 𝐌𝐄𝐍𝐔\n\n"
            "/start — Main menu\n"
            "/id — Chat ID\n"
            "/info — Bot information\n"
            "/help — Help menu\n"
            "/owner — Owner\n"
            "/channel — Official channel"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🏠 HOME",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "home":
        text = (
            "╔════════════════════════════╗\n"
            "        ✦ 𝐉𝐎𝐘 𝐖𝐄𝐁 𝐁𝐎𝐓 ✦\n"
            "╚════════════════════════════╝\n\n"

            f"👋 Welcome, {user.first_name}!\n\n"

            "🔥 Official JOY WEB Bot\n"
            "⚡ Fast • Simple • Secure\n\n"

            "📌 Commands:\n"
            "🆔 /id\n"
            "ℹ️ /info\n"
            "🆘 /help\n"
            "👑 /owner\n"
            "📢 /channel"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🆔 MY ID",
                    callback_data="my_id"
                ),
                InlineKeyboardButton(
                    "ℹ️ INFO",
                    callback_data="info"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🆘 HELP",
                    callback_data="help"
                ),
                InlineKeyboardButton(
                    "👑 OWNER",
                    url="https://t.me/JOYxWEB"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📢 CHANNEL",
                    url=CHANNEL_URL
                )
            ],
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("id", get_id)
    )

    application.add_handler(
        CommandHandler("info", info)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("owner", owner)
    )

    application.add_handler(
        CommandHandler("channel", channel)
    )

    application.add_handler(
        # Inline button handler
        __import__(
            "telegram.ext",
            fromlist=["CallbackQueryHandler"]
        ).CallbackQueryHandler(button_handler)
    )

    application.add_error_handler(error_handler)

    print("🚀 JOY WEB BOT is starting...")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()