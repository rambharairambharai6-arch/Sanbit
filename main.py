import logging
import platform
import time
import json
import os
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ─────────────────────────────────────────────
#  ⚙️  LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("JoyWebs")

# ─────────────────────────────────────────────
#  🔧  CONFIGURATION
# ─────────────────────────────────────────────
BOT_TOKEN        = "8293793841:AAFrKiukw_OqwXzGsFf4ZAI2jSfPEAdobro"   # ⚠️ REVOKE & REPLACE
OWNER_USERNAME   = "@JOYxWEB"
OWNER_ID         = 7774294727                # 👑 Owner's numeric Telegram ID
CHANNEL_USERNAME = "@JOY_WEBS"
CHANNEL_ID       = -1002904389369
PREMIUM_USERS    = []                       # add premium user IDs, e.g. [123456789]
START_TIME       = time.time()
BOT_VERSION      = "v2.0 Premium"
USERS_FILE       = "users.json"             # 📁 broadcast user list

# ─────────────────────────────────────────────
#  💎  BRANDING
# ─────────────────────────────────────────────
BOT_NAME = "𝐉𝐎𝐘 𝐖𝐄𝐁𝐒"
DIVIDER  = "━━━━━━━━━━━━━━━━━━━━━━━"
THIN     = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
SPARKLE  = "✨"
CROWN    = "👑"
LOCK     = "🔒"
CHECK    = "✅"
CROSS    = "❌"
ID_EMOJI = "🆔"
MEGA     = "📣"
STAR     = "⭐"
FIRE     = "🔥"
DIAMOND  = "💎"
ROCKET   = "🚀"
GLOBE    = "🌐"
CLOCK    = "🕒"
GEAR     = "⚙️"
INFO     = "ℹ️"
SHIELD   = "🛡️"
GIFT     = "🎁"
BOLT     = "⚡"
HEART    = "💖"
TROPHY   = "🏆"

# ─────────────────────────────────────────────
#  💾  USER STORAGE (for broadcast)
# ─────────────────────────────────────────────
def load_users() -> set:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            logger.warning(f"Could not load users: {e}")
    return set()


def save_users(users: set) -> None:
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(users), f)
    except Exception as e:
        logger.warning(f"Could not save users: {e}")


def add_user(user_id: int) -> None:
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        save_users(users)


# ─────────────────────────────────────────────
#  🛠️  HELPERS
# ─────────────────────────────────────────────
async def is_user_joined(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning(f"Membership check failed for {user_id}: {e}")
        return False


def is_premium(user_id: int) -> bool:
    return user_id in PREMIUM_USERS


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"{MEGA}  ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ  {MEGA}",
                                  url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton(f"{CHECK}  ᴠᴇʀɪꜰʏ ᴀᴄᴄᴇꜱꜱ  {CHECK}",
                                  callback_data="verify")],
        ]
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"{ID_EMOJI} ᴍʏ ɪᴅ", callback_data="show_id"),
                InlineKeyboardButton(f"{INFO} ᴀʙᴏᴜᴛ", callback_data="about"),
            ],
            [
                InlineKeyboardButton(f"{GEAR} ᴄᴏᴍᴍᴀɴᴅꜱ", callback_data="commands"),
                InlineKeyboardButton(f"{SHIELD} ꜱᴛᴀᴛᴜꜱ", callback_data="status"),
            ],
            [
                InlineKeyboardButton(f"{MEGA} ᴄʜᴀɴɴᴇʟ",
                                     url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
                InlineKeyboardButton(f"{CROWN} ᴏᴡɴᴇʀ",
                                     url=f"https://t.me/{OWNER_USERNAME.lstrip('@')}"),
            ],
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{BOLT} ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="menu")]]
    )


# ─────────────────────────────────────────────
#  📝  TEXT TEMPLATES
# ─────────────────────────────────────────────
def welcome_text(first_name: str) -> str:
    return (
        f"<b>{DIVIDER}</b>\n"
        f"      {CROWN}  <b>{BOT_NAME}</b>  {CROWN}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{SPARKLE} <b>Hello, {first_name}!</b>\n\n"
        f"{CHECK} You are now <b>verified</b>.\n"
        f"{DIAMOND} Premium access <b>unlocked</b>.\n"
        f"{FIRE} Enjoy the full experience!\n\n"
        f"<b>{THIN}</b>\n"
        f"{GEAR} <b>Quick Access</b>\n"
        f"<b>{THIN}</b>\n"
        f"  {ID_EMOJI} /id       — ɢᴇᴛ ʏᴏᴜʀ ᴄʜᴀᴛ ɪᴅ\n"
        f"  {INFO} /about    — ᴀʙᴏᴜᴛ ᴛʜɪꜱ ʙᴏᴛ\n"
        f"  {GEAR} /commands — ꜰᴜʟʟ ᴄᴏᴍᴍᴀɴᴅ ʟɪꜱᴛ\n"
        f"  {SHIELD} /status   — ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ\n"
        f"  {GIFT} /premium  — ᴘʀᴇᴍɪᴜᴍ ɪɴꜰᴏ\n"
        f"  {HEART} /support  — ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ\n\n"
        f"<i>{SPARKLE} Tap a button below to begin 👇</i>"
    )


def locked_text(first_name: str) -> str:
    return (
        f"<b>{DIVIDER}</b>\n"
        f"      {LOCK}  <b>ᴀᴄᴄᴇꜱꜱ ʟᴏᴄᴋᴇᴅ</b>  {LOCK}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{SPARKLE} Hey <b>{first_name}</b>,\n\n"
        f"{CROSS} You must <b>join our channel</b>\n"
        f"first to unlock <b>{BOT_NAME}</b>.\n\n"
        f"<b>{THIN}</b>\n"
        f"{MEGA} <b>Channel:</b> {CHANNEL_USERNAME}\n"
        f"{CROWN} <b>Owner:</b> {OWNER_USERNAME}\n"
        f"<b>{THIN}</b>\n\n"
        f"<i>Join below, then tap {CHECK} Verify 👇</i>"
    )


# ─────────────────────────────────────────────
#  🚀  CORE HANDLERS
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    add_user(user.id)   # 💾 save for broadcast

    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name),
            parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
            disable_web_page_preview=True,
        )
        return

    await update.message.reply_text(
        welcome_text(user.first_name),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True,
    )


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    add_user(user.id)   # 💾 save

    if not await is_user_joined(context.bot, user.id):
        await query.answer("❌ You haven't joined yet!", show_alert=True)
        await query.edit_message_text(
            locked_text(user.first_name),
            parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
            disable_web_page_preview=True,
        )
        return

    await query.answer("✅ Verified successfully!", show_alert=False)
    await query.edit_message_text(
        welcome_text(user.first_name),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────
#  🆔  /id  +  CALLBACK
# ─────────────────────────────────────────────
def build_id_card(chat_id: int, user) -> str:
    username = f"@{user.username}" if user.username else "—"
    return (
        f"<b>{DIVIDER}</b>\n"
        f"      {ID_EMOJI}  <b>ᴄʜᴀᴛ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ</b>  {ID_EMOJI}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{MEGA} <b>Chat ID:</b>  <code>{chat_id}</code>\n"
        f"👤 <b>User ID:</b>  <code>{user.id}</code>\n"
        f"{STAR} <b>Username:</b>  {username}\n"
        f"{CROWN} <b>Name:</b>  {user.full_name}\n\n"
        f"<b>{THIN}</b>\n"
        f"<i>{SPARKLE} Powered by {BOT_NAME}</i>"
    )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name),
            parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return

    await update.message.reply_text(
        build_id_card(update.effective_chat.id, user),
        parse_mode=ParseMode.HTML,
    )


async def show_id_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        build_id_card(query.message.chat_id, query.from_user),
        parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(),
    )


# ─────────────────────────────────────────────
#  ℹ️  /about
# ─────────────────────────────────────────────
def about_text() -> str:
    return (
        f"<b>{DIVIDER}</b>\n"
        f"      {INFO}  <b>ᴀʙᴏᴜᴛ {BOT_NAME}</b>  {INFO}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{DIAMOND} <b>Name:</b>  {BOT_NAME}\n"
        f"{ROCKET} <b>Version:</b>  {BOT_VERSION}\n"
        f"{CROWN} <b>Owner:</b>  {OWNER_USERNAME}\n"
        f"{MEGA} <b>Channel:</b>  {CHANNEL_USERNAME}\n\n"
        f"<b>{THIN}</b>\n"
        f"{SPARKLE} A premium Telegram bot built for\n"
        f"speed, style, and reliability.\n"
        f"<b>{THIN}</b>\n\n"
        f"<i>{HEART} Made with love by {OWNER_USERNAME}</i>"
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return
    await update.message.reply_text(about_text(), parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True)


async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        about_text(), parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(), disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────
#  ⚙️  /commands  —  FULL LIST
# ─────────────────────────────────────────────
def commands_text() -> str:
    return (
        f"<b>{DIVIDER}</b>\n"
        f"      {GEAR}  <b>ᴄᴏᴍᴍᴀɴᴅ ᴍᴇɴᴜ</b>  {GEAR}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{TROPHY} <b>MAIN COMMANDS</b>\n"
        f"<b>{THIN}</b>\n"
        f"  {ROCKET} /start      — ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n"
        f"  {INFO} /help       — ꜱʜᴏᴡ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
        f"  {GEAR} /commands   — ꜰᴜʟʟ ᴄᴏᴍᴍᴀɴᴅ ʟɪꜱᴛ\n"
        f"  {ID_EMOJI} /id         — ɢᴇᴛ ᴄʜᴀᴛ ɪᴅ\n"
        f"  {INFO} /about      — ᴀʙᴏᴜᴛ ᴛʜɪꜱ ʙᴏᴛ\n\n"

        f"{DIAMOND} <b>PREMIUM COMMANDS</b>\n"
        f"<b>{THIN}</b>\n"
        f"  {GIFT} /premium    — ᴘʀᴇᴍɪᴜᴍ ɪɴꜰᴏ\n"
        f"  {SHIELD} /status     — ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ\n"
        f"  {CLOCK} /uptime     — ʙᴏᴛ ᴜᴘᴛɪᴍᴇ\n"
        f"  {GLOBE} /ping       — ʟᴀᴛᴇɴᴄʏ ᴛᴇꜱᴛ\n"
        f"  {HEART} /support    — ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ\n\n"

        f"{CROWN} <b>OWNER</b>\n"
        f"<b>{THIN}</b>\n"
        f"  {CROWN} /owner      — ᴏᴡɴᴇʀ ɪɴꜰᴏ\n"
        f"  {MEGA} /broadcast  — ꜱᴇɴᴅ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀꜱ\n"
        f"  {STAR} /users      — ᴛᴏᴛᴀʟ ᴜꜱᴇʀ ᴄᴏᴜɴᴛ\n\n"

        f"<b>{DIVIDER}</b>\n"
        f"<i>{SPARKLE} {BOT_NAME} • {BOT_VERSION}</i>"
    )


async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return
    await update.message.reply_text(commands_text(), parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True)


async def commands_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        commands_text(), parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(), disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────
#  ℹ️  /help
# ─────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return
    await update.message.reply_text(
        commands_text(), parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(), disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────
#  💎  /premium
# ─────────────────────────────────────────────
def premium_text(user_id: int) -> str:
    status = f"{CHECK} <b>Active</b>" if is_premium(user_id) else f"{CROSS} <b>Not Active</b>"
    return (
        f"<b>{DIVIDER}</b>\n"
        f"      {GIFT}  <b>ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ</b>  {GIFT}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{DIAMOND} <b>Your Status:</b>  {status}\n\n"
        f"<b>{THIN}</b>\n"
        f"{TROPHY} <b>PREMIUM PERKS</b>\n"
        f"<b>{THIN}</b>\n"
        f"  {BOLT} Faster responses\n"
        f"  {STAR} Exclusive commands\n"
        f"  {SHIELD} Priority support\n"
        f"  {GIFT} Early access to features\n\n"
        f"<b>{THIN}</b>\n"
        f"{CROWN} <b>Get Premium:</b> {OWNER_USERNAME}\n\n"
        f"<i>{SPARKLE} Unlock the full {BOT_NAME} experience.</i>"
    )


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return
    await update.message.reply_text(
        premium_text(user.id), parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────
#  🛡️  /status  +  ⏱  /uptime  +  🌐  /ping
# ─────────────────────────────────────────────
def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, s = divmod(seconds, 60)
    parts = []
    if d: parts.append(f"{d}ᴅ")
    if h: parts.append(f"{h}ʜ")
    if m: parts.append(f"{m}ᴍ")
    parts.append(f"{s}ꜱ")
    return " ".join(parts)


def status_text() -> str:
    return (
        f"<b>{DIVIDER}</b>\n"
        f"      {SHIELD}  <b>ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ</b>  {SHIELD}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{CHECK} <b>Status:</b>  Online\n"
        f"{ROCKET} <b>Version:</b>  {BOT_VERSION}\n"
        f"{CLOCK} <b>Uptime:</b>  {format_uptime(time.time() - START_TIME)}\n"
        f"{GLOBE} <b>Platform:</b>  {platform.system()}\n"
        f"{GEAR} <b>Python:</b>  {platform.python_version()}\n\n"
        f"<b>{THIN}</b>\n"
        f"{SPARKLE} All systems operational.\n"
        f"<i>{HEART} {BOT_NAME} running smoothly.</i>"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return
    await update.message.reply_text(status_text(), parse_mode=ParseMode.HTML)


async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        status_text(), parse_mode=ParseMode.HTML,
        reply_markup=back_keyboard(),
    )


async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return
    await update.message.reply_text(
        f"<b>{DIVIDER}</b>\n"
        f"      {CLOCK}  <b>ʙᴏᴛ ᴜᴘᴛɪᴍᴇ</b>  {CLOCK}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{ROCKET} <b>Running for:</b>\n"
        f"<code>{format_uptime(time.time() - START_TIME)}</code>\n\n"
        f"<i>{SPARKLE} {BOT_NAME} — always online.</i>",
        parse_mode=ParseMode.HTML,
    )


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return

    start = time.perf_counter()
    msg = await update.message.reply_text(f"{BOLT} <b>Pinging...</b>", parse_mode=ParseMode.HTML)
    latency = (time.perf_counter() - start) * 1000

    quality = "🟢 Excellent" if latency < 200 else "🟡 Good" if latency < 500 else "🔴 Slow"
    await msg.edit_text(
        f"<b>{DIVIDER}</b>\n"
        f"      {GLOBE}  <b>ʟᴀᴛᴇɴᴄʏ ᴛᴇꜱᴛ</b>  {GLOBE}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{BOLT} <b>Ping:</b>  <code>{latency:.2f} ms</code>\n"
        f"{STAR} <b>Quality:</b>  {quality}\n\n"
        f"<i>{SPARKLE} {BOT_NAME} response speed.</i>",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────
#  ❤️  /support  +  👑  /owner
# ─────────────────────────────────────────────
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{CROWN} ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ",
                               url=f"https://t.me/{OWNER_USERNAME.lstrip('@')}")]]
    )
    await update.message.reply_text(
        f"<b>{DIVIDER}</b>\n"
        f"      {HEART}  <b>ꜱᴜᴘᴘᴏʀᴛ ᴄᴇɴᴛᴇʀ</b>  {HEART}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{SPARKLE} Need help? We're here for you!\n\n"
        f"<b>{THIN}</b>\n"
        f"{CROWN} <b>Owner:</b> {OWNER_USERNAME}\n"
        f"{MEGA} <b>Channel:</b> {CHANNEL_USERNAME}\n"
        f"<b>{THIN}</b>\n\n"
        f"<i>{STAR} Expect a reply within 24 hours.</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not await is_user_joined(context.bot, user.id):
        await update.message.reply_text(
            locked_text(user.first_name), parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(),
        )
        return

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{CROWN} ᴍᴇꜱꜱᴀɢᴇ ᴏᴡɴᴇʀ",
                               url=f"https://t.me/{OWNER_USERNAME.lstrip('@')}")]]
    )
    # ✅ COMPLETED BLOCK: All parentheses closed and message added
    await update.message.reply_text(
        f"<b>{DIVIDER}</b>\n"
        f"      {CROWN}  <b>ᴏᴡɴᴇʀ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ</b>  {CROWN}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{SPARKLE} <b>Owner:</b> {OWNER_USERNAME}\n"
        f"{MEGA} <b>Channel:</b> {CHANNEL_USERNAME}\n\n"
        f"{THIN}\n"
        f"<i>{HEART} Click below to send a direct message.</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────
#  👑  /broadcast  +  📊  /users  (Owner only)
# ─────────────────────────────────────────────
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update.effective_user.id):
        await update.message.reply_text(f"{CROSS} <b>Owner only command.</b>", parse_mode=ParseMode.HTML)
        return

    if not context.args:
        await update.message.reply_text(
            f"<b>{DIVIDER}</b>\n"
            f"      {MEGA}  <b>ʙʀᴏᴀᴅᴄᴀꜱᴛ</b>  {MEGA}\n"
            f"<b>{DIVIDER}</b>\n\n"
            f"{INFO} <b>Usage:</b> <code>/broadcast Your message here</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    message = " ".join(context.args)
    users = load_users()
    sent, failed = 0, 0

    status_msg = await update.message.reply_text(f"{ROCKET} Broadcasting to {len(users)} users...")

    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"<b>{DIVIDER}</b>\n"
                     f"      {MEGA}  <b>ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ</b>  {MEGA}\n"
                     f"<b>{DIVIDER}</b>\n\n"
                     f"{message}\n\n"
                     f"<i>{SPARKLE} — {BOT_NAME}</i>",
                parse_mode=ParseMode.HTML,
            )
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"<b>{DIVIDER}</b>\n"
        f"      {CHECK}  <b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇ</b>  {CHECK}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{CHECK} <b>Sent:</b> {sent}\n"
        f"{CROSS} <b>Failed:</b> {failed}\n"
        f"{MEGA} <b>Total:</b> {len(users)}",
        parse_mode=ParseMode.HTML,
    )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update.effective_user.id):
        await update.message.reply_text(f"{CROSS} <b>Owner only command.</b>", parse_mode=ParseMode.HTML)
        return

    users = load_users()
    await update.message.reply_text(
        f"<b>{DIVIDER}</b>\n"
        f"      {STAR}  <b>ᴜꜱᴇʀ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ</b>  {STAR}\n"
        f"<b>{DIVIDER}</b>\n\n"
        f"{MEGA} <b>Total Users:</b> <code>{len(users)}</code>\n\n"
        f"<i>{SPARKLE} {BOT_NAME} database</i>",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────
#  🔘  MENU CALLBACK
# ─────────────────────────────────────────────
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    await query.edit_message_text(
        welcome_text(user.first_name),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────
#  🚀  MAIN
# ─────────────────────────────────────────────
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("commands", commands_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("uptime", uptime_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("owner", owner_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("users", users_command))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify$"))
    application.add_handler(CallbackQueryHandler(show_id_callback, pattern="^show_id$"))
    application.add_handler(CallbackQueryHandler(about_callback, pattern="^about$"))
    application.add_handler(CallbackQueryHandler(commands_callback, pattern="^commands$"))
    application.add_handler(CallbackQueryHandler(status_callback, pattern="^status$"))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))

    logger.info(f"🚀 {BOT_NAME} {BOT_VERSION} is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()