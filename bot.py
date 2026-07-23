import asyncio
import csv
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# ==========================================================
# BASIC SETTINGS
# ==========================================================
BOT_TOKEN = "8804269999:AAFXkBFPxYpIrd3WlcBnyDuvoktxGoATzXI"
ADMIN_ID = 8853901359

# Start page photo aur QR. Baad me apne links/file_id laga sakte ho.
MAIN_PHOTO = "https://ne6-bd9be46d442c.herokuapp.com/stream/2512388?hash=493c7c&d=true"
QR_PHOTO = "https://ibb.co/n5RksVK"
UPI_ID = "paytm.s1t251t@pty"

# ==========================================================
# PACKAGES
# ==========================================================
PACKAGES = {
    "CHILD": {
        "name": "CHILD P@RN",
        "button": "CHILD P@RN ₹99",
        "price": "₹99",
        "videos": "4000 𝑽𝑰𝑫𝑬𝑶𝑺",
        "links": "https://t.me/+mVGZjernjvVjOTQ1",
    },
    "mms": {
        "name": "MMS ONLY",
        "button": "MMS ONLY ₹149",
        "price": "₹149",
        "videos": "3000 𝑽𝑰𝑫𝑬𝑶𝑺",
        "links": "https://t.me/+Zun6rt3fDsM1Njc1",
    },
    "viral": {
        "name": "MMS + INSTA VIRAL",
        "button": "MMS + INSTA VIRAL ₹199",
        "price": "₹199",
        "videos": "8000 𝑽𝑰𝑫𝑬𝑶𝑺",
        "links": "https://t.me/+5oD7J1aGiPM1N2M1",
    },
    "mix": {
        "name": "MIX ( CHILD P@RN + MMS )",
        "button": "MIX ( CHILD P@RN + MMS ) ₹199",
        "price": "₹199",
        "videos": "15𝑲 𝑽𝑰𝑫𝑬𝑶𝑺",
        "links": "LINK 1 :-\nhttps://t.me/+5oD7J1aGiPM1N2M1\n\nLINK 2 :-\nhttps://t.me/+mVGZjernjvVjOTQ1",
    },
    "ACTRESS+HIDDEN CAMERA": {
        "name": "ACTRESS+HIDDEN CAMERA",
        "button": "ACTRESS+HIDDEN CAMERA ₹179",
        "price": "₹179",
        "videos": "2500 𝑽𝑰𝑫𝑬𝑶𝑺",
        "links": "https://t.me/+glLeZjt1iJ9lZDY1",
    },
    "ALL 20 GROUPS": {
        "name": "ALL 20 GROUPS",
        "button": "ALL 20 GROUPS ₹459",
        "price": "₹459",
        "videos": "30K 𝑽𝑰𝑫𝑬𝑶𝑺",
        "links": "https://t.me/addlist/8Uaa5HLfoL1lYTc1",
    },
}

# ==========================================================
# DATABASE + DEMO DATA
# ==========================================================
DB_FILE = Path("bot_database.db")
DEMO_FILE = Path("demo_data.json")

DEMO_LIMITS = {
    "mms": {"name": "MMS DEMO", "photos": 5, "videos": 4},
    "CHILD": {"name": "CHILD P@RN DEMO", "photos": 5, "videos": 3},
}

def now_utc():
    return datetime.now(timezone.utc)

def now_iso():
    return now_utc().isoformat(timespec="seconds")

def db_connect():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    return db

def init_database():
    with db_connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                username TEXT,
                language_code TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                package_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'selected',
                selected_at TEXT NOT NULL,
                screenshot_at TEXT,
                screenshot_file_id TEXT,
                screenshot_type TEXT,
                reviewed_at TEXT
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sent_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        db.commit()

def save_or_update_user(user):
    if not user:
        return
    ts = now_iso()
    with db_connect() as db:
        old = db.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,)).fetchone()
        if old:
            db.execute("""
                UPDATE users
                SET first_name=?, username=?, language_code=?, is_active=1, last_seen=?
                WHERE user_id=?
            """, (user.first_name or "User", user.username, user.language_code, ts, user.id))
        else:
            db.execute("""
                INSERT INTO users (user_id, first_name, username, language_code, is_active, first_seen, last_seen)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (user.id, user.first_name or "User", user.username, user.language_code, ts, ts))
        db.commit()

def deactivate_user(user_id):
    with db_connect() as db:
        db.execute("UPDATE users SET is_active=0 WHERE user_id=?", (user_id,))
        db.commit()

def create_order(user_id, package_key):
    with db_connect() as db:
        cur = db.execute("""
            INSERT INTO orders (user_id, package_key, status, selected_at)
            VALUES (?, ?, 'selected', ?)
        """, (user_id, package_key, now_iso()))
        db.commit()
        return int(cur.lastrowid)

def latest_selected_order(user_id):
    with db_connect() as db:
        return db.execute("""
            SELECT * FROM orders
            WHERE user_id=? AND status='selected'
            ORDER BY order_id DESC
            LIMIT 1
        """, (user_id,)).fetchone()

def get_order(order_id):
    with db_connect() as db:
        return db.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()

def submit_order(order_id, file_id, screenshot_type):
    with db_connect() as db:
        db.execute("""
            UPDATE orders
            SET status='submitted', screenshot_at=?, screenshot_file_id=?, screenshot_type=?
            WHERE order_id=?
        """, (now_iso(), file_id, screenshot_type, order_id))
        db.commit()

def update_order_status(order_id, status):
    with db_connect() as db:
        db.execute("UPDATE orders SET status=?, reviewed_at=? WHERE order_id=?", (status, now_iso(), order_id))
        db.commit()

def fresh_demo_data():
    return {"recording": None, "demos": {"mms": {"photos": [], "videos": []}, "CHILD": {"photos": [], "videos": []}}}

def load_demo_data():
    if DEMO_FILE.exists():
        try:
            data = json.loads(DEMO_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = fresh_demo_data()
    else:
        data = fresh_demo_data()

    data.setdefault("recording", None)
    data.setdefault("demos", {})
    for key in DEMO_LIMITS:
        data["demos"].setdefault(key, {"photos": [], "videos": []})
        data["demos"][key].setdefault("photos", [])
        data["demos"][key].setdefault("videos", [])
    return data

DEMO_DATA = load_demo_data()

def save_demo_data():
    DEMO_FILE.write_text(json.dumps(DEMO_DATA, indent=2, ensure_ascii=False), encoding="utf-8")

# ==========================================================
# TEXT + BUTTONS
# ==========================================================
START_TEXT = """
🔥 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗠𝗠𝗦 🔥

✅ 𝟭𝟬𝟬% 𝗧𝗥𝗨𝗦𝗧𝗘𝗗 𝗦𝗘𝗟𝗟𝗜𝗡𝗚 ✅ 

💥 100k+ VIDEOS AVILABLE 
💥 CHILD P@RN
💥 MMS ADULT 
💥 ACTRESS INDIAN 
💥 HIDDEN CAMERA
💥 ADULT GIRLS
💥 BROTHER SISTER 
💥 DESI VIRAL
💥 RAPE CASE 
💥 GROUP SEX

👇 CHOOSE AN OPTION BELOW 👇
"""

BUY_TEXT = """
🔥 BUY FROM HERE ALL TYPE 🔥

👇 SELECT YOUR PACKAGE
"""

def start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("BUY PREMIUM VIDEOS", callback_data="buy")],
        [
            InlineKeyboardButton("MMS DEMO", callback_data="demo|mms"),
            InlineKeyboardButton("CHILD P@RN DEMO", callback_data="demo|CHILD"),
        ],
    ])

def buy_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(PACKAGES["CHILD"]["button"], callback_data="package|CHILD")],
        [InlineKeyboardButton(PACKAGES["mms"]["button"], callback_data="package|mms")],
        [InlineKeyboardButton(PACKAGES["viral"]["button"], callback_data="package|viral")],
        [InlineKeyboardButton(PACKAGES["mix"]["button"], callback_data="package|mix")],
        [InlineKeyboardButton(PACKAGES["ACTRESS+HIDDEN CAMERA"]["button"], callback_data="package|ACTRESS+HIDDEN CAMERA")],
        [InlineKeyboardButton(PACKAGES["ALL 20 GROUPS"]["button"], callback_data="package|ALL 20 GROUPS")],
        [InlineKeyboardButton("🔙 BACK", callback_data="home")],
    ])

def payment_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 SEND PAYMENT SCREENSHOT", callback_data="send_screenshot")],
        [InlineKeyboardButton("🔙 BACK", callback_data="buy")],
    ])

def buy_only_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔥 BUY PREMIUM VIDEOS 🔥", callback_data="buy")]])

# ==========================================================
# USER SIDE
# ==========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_or_update_user(update.effective_user)
    await update.message.reply_photo(photo=MAIN_PHOTO, caption=START_TEXT, reply_markup=start_buttons())

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deactivate_user(update.effective_user.id)
    await update.message.reply_text("✅ Aapko broadcast list se remove kar diya gaya. /start bhejoge to dobara add ho jaoge.")

async def show_home(query):
    await query.message.edit_media(media=InputMediaPhoto(media=MAIN_PHOTO, caption=START_TEXT), reply_markup=start_buttons())

async def show_buy_menu(query):
    await query.message.edit_media(media=InputMediaPhoto(media=MAIN_PHOTO, caption=BUY_TEXT), reply_markup=buy_buttons())

async def show_payment_page(query, package_key):
    package = PACKAGES[package_key]
    create_order(query.from_user.id, package_key)

    caption = f"""
🔥 PAYMENT DETAILS 🔥

📦 CATEGORY : {package["name"]}

💰 PRICE : {package["price"]} FOR {package["videos"]}

━━━━━━━━━━━━━━

💳 UPI ID :- <code>{UPI_ID}</code>

━━━━━━━━━━━━━━

✅ AFTER PAYMENT : SEND SCREENSHOT 💥
🎊 GET LINK AFTER CONFIRMATION ✅
"""
    await query.message.edit_media(
        media=InputMediaPhoto(media=QR_PHOTO, caption=caption, parse_mode=ParseMode.HTML),
        reply_markup=payment_buttons()
    )

async def send_demo_to_chat(context, chat_id, demo_key):
    demo = DEMO_DATA["demos"][demo_key]
    limit = DEMO_LIMITS[demo_key]
    name = limit["name"]

    if len(demo["photos"]) < limit["photos"] or len(demo["videos"]) < limit["videos"]:
        return False, f"{name} abhi ready nahi hai."

    for photo_id in demo["photos"][:limit["photos"]]:
        await context.bot.send_photo(chat_id=chat_id, photo=photo_id)

    videos = demo["videos"][:limit["videos"]]
    for i, video_id in enumerate(videos):
        if i == len(videos) - 1:
            await context.bot.send_video(chat_id=chat_id, video=video_id, supports_streaming=True, reply_markup=buy_only_button())
        else:
            await context.bot.send_video(chat_id=chat_id, video=video_id, supports_streaming=True)

    return True, "sent"

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    save_or_update_user(query.from_user)

    if data == "home":
        await query.answer()
        await show_home(query)
        return

    if data == "buy":
        await query.answer()
        await show_buy_menu(query)
        return

    if data.startswith("demo|"):
        demo_key = data.split("|", 1)[1]
        await query.answer("Demo sending...")
        ok, msg = await send_demo_to_chat(context, query.message.chat_id, demo_key)
        if not ok:
            await query.message.reply_text("❌ " + msg)
        return

    if data.startswith("package|"):
        await query.answer()
        package_key = data.split("|", 1)[1]
        if package_key not in PACKAGES:
            await query.answer("Package not found.", show_alert=True)
            return
        await show_payment_page(query, package_key)
        return

    if data == "send_screenshot":
        await query.answer("Ab payment screenshot isi bot ko send karo.", show_alert=True)
        return

    if data.startswith("approve|"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("Only admin can approve.", show_alert=True)
            return
        order_id = int(data.split("|", 1)[1])
        order = get_order(order_id)
        if not order or order["status"] != "submitted":
            await query.answer("Ye order already process ho chuka hai ya invalid hai.", show_alert=True)
            return
        package = PACKAGES[order["package_key"]]
        await context.bot.send_message(
            chat_id=order["user_id"],
            text="✅ PAYMENT CONFIRMED\n\n🎊 HERE IS YOUR PREMIUM LINK 👇\n\n" + package["links"]
        )
        update_order_status(order_id, "approved")
        await query.message.edit_caption(caption=(query.message.caption or "") + "\n\n✅ APPROVED — LINK SENT", reply_markup=None)
        await query.answer("Link sent successfully ✅", show_alert=True)
        return

    if data.startswith("reject|"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("Only admin can reject.", show_alert=True)
            return
        order_id = int(data.split("|", 1)[1])
        order = get_order(order_id)
        if not order or order["status"] != "submitted":
            await query.answer("Ye order already process ho chuka hai ya invalid hai.", show_alert=True)
            return
        await context.bot.send_message(chat_id=order["user_id"], text="❌ PAYMENT NOT VERIFIED\n\nPlease contact admin.")
        update_order_status(order_id, "rejected")
        await query.message.edit_caption(caption=(query.message.caption or "") + "\n\n❌ REJECTED", reply_markup=None)
        await query.answer("Payment rejected ❌", show_alert=True)

# ==========================================================
# SCREENSHOT HANDLER
# ==========================================================
async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = update.effective_user

    if user.id == ADMIN_ID:
        return

    save_or_update_user(user)
    order = latest_selected_order(user.id)

    if not order:
        await message.reply_text("❌ Pehle BUY PREMIUM VIDEOS me package select karo, phir screenshot bhejo.")
        return

    package = PACKAGES[order["package_key"]]
    username = f"@{user.username}" if user.username else "Not Set"

    admin_buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ CONFIRM", callback_data=f"approve|{order['order_id']}"),
        InlineKeyboardButton("❌ REJECT", callback_data=f"reject|{order['order_id']}"),
    ]])

    caption = (
        "🔥 NEW PAYMENT SCREENSHOT 🔥\n\n"
        f"👤 NAME : {user.first_name or 'User'}\n"
        f"🔖 USERNAME : {username}\n"
        f"🆔 USER ID : {user.id}\n\n"
        f"📦 PACKAGE : {package['name']}\n"
        f"💰 PRICE : {package['price']}\n"
        f"🧾 ORDER ID : {order['order_id']}"
    )

    if message.photo:
        file_id = message.photo[-1].file_id
        submit_order(order["order_id"], file_id, "photo")
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=admin_buttons)
    else:
        file_id = message.document.file_id
        submit_order(order["order_id"], file_id, "document")
        await context.bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=caption, reply_markup=admin_buttons)

    await message.reply_text("✅ SCREENSHOT SENT TO ADMIN\n\nYOU WILL GET THE LINK AFTER VERIFICATION.")

# ==========================================================
# ADMIN DEMO RECORDING
# ==========================================================
def is_admin(update):
    return update.effective_user and update.effective_user.id == ADMIN_ID

async def record_mms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    DEMO_DATA["demos"]["mms"] = {"photos": [], "videos": []}
    DEMO_DATA["recording"] = "mms"
    save_demo_data()
    await update.message.reply_text("✅ MMS DEMO RESET + RECORDING STARTED\n\nPehle 5 photos bhejo, phir 4 videos bhejo.")

async def record_CHILD(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    DEMO_DATA["demos"]["CHILD"] = {"photos": [], "videos": []}
    DEMO_DATA["recording"] = "CHILD"
    save_demo_data()
    await update.message.reply_text("✅ CHILD P@RN DEMO RESET + RECORDING STARTED\n\nPehle 5 photos bhejo, phir 3 videos bhejo.")

async def demo_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    mms = DEMO_DATA["demos"]["mms"]
    CHILD = DEMO_DATA["demos"]["CHILD"]
    rec = DEMO_DATA.get("recording")
    rec_name = DEMO_LIMITS[rec]["name"] if rec else "OFF"
    await update.message.reply_text(
        f"📊 DEMO STATUS\n\n"
        f"MMS DEMO: {len(mms['photos'])}/5 photos, {len(mms['videos'])}/4 videos\n"
        f"CHILD P@RN DEMO: {len(CHILD['photos'])}/5 photos, {len(CHILD['videos'])}/3 videos\n\n"
        f"Recording Now: {rec_name}"
    )

async def stop_recording(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    DEMO_DATA["recording"] = None
    save_demo_data()
    await update.message.reply_text("⏹ Recording stopped.")

async def test_mms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    ok, msg = await send_demo_to_chat(context, update.effective_chat.id, "mms")
    if not ok: await update.message.reply_text("❌ " + msg)

async def test_CHILD(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    ok, msg = await send_demo_to_chat(context, update.effective_chat.id, "CHILD")
    if not ok: await update.message.reply_text("❌ " + msg)

async def save_demo_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    message = update.message
    recording = DEMO_DATA.get("recording")
    if not recording:
        # Admin photo ko screenshot nahi samjhega; sirf bata dega.
        await message.reply_text("❌ Recording OFF hai. Pehle /record_mms ya /record_CHILD bhejo.")
        return

    demo = DEMO_DATA["demos"][recording]
    limit = DEMO_LIMITS[recording]
    name = limit["name"]

    if message.photo:
        if len(demo["photos"]) >= limit["photos"]:
            await message.reply_text(f"✅ {name} photos complete hain. Ab videos bhejo.")
            return
        demo["photos"].append(message.photo[-1].file_id)
        save_demo_data()
        await message.reply_text(f"✅ {name} PHOTO SAVED: {len(demo['photos'])}/{limit['photos']}")
        return

    if message.video:
        if len(demo["photos"]) < limit["photos"]:
            await message.reply_text(f"❌ Pehle photos complete karo. Photos: {len(demo['photos'])}/{limit['photos']}")
            return
        if len(demo["videos"]) >= limit["videos"]:
            await message.reply_text(f"✅ {name} videos already complete hain.")
            return
        demo["videos"].append(message.video.file_id)
        save_demo_data()
        await message.reply_text(f"✅ {name} VIDEO SAVED: {len(demo['videos'])}/{limit['videos']}")
        if len(demo["videos"]) == limit["videos"]:
            DEMO_DATA["recording"] = None
            save_demo_data()
            await message.reply_text(f"🎉 {name} READY HO GAYA!")
        return

    if message.document:
        await message.reply_text("❌ File/document mode nahi. Gallery se normal video/photo bhejo.")

# ==========================================================
# ADMIN STATS + BROADCAST
# ==========================================================
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    await update.message.reply_text(
        "🛠 ADMIN COMMANDS\n\n"
        "/stats - Users + payment stats\n"
        "/users - Same as stats\n"
        "/recent - Recent 10 users\n"
        "/pending - Pending payment screenshots\n"
        "/broadcast Your message - Sab active users ko message\n"
        "/record_mms - MMS demo save\n"
        "/record_CHILD - CHILD P@RN demo save\n"
        "/demo_status - Demo status\n"
        "/test_mms - Test MMS demo\n"
        "/test_CHILD - Test CHILD P@RN demo"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    today = now_utc().date().isoformat()
    yesterday = (now_utc() - timedelta(days=1)).date().isoformat()

    with db_connect() as db:
        total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active = db.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]
        today_users = db.execute("SELECT COUNT(*) FROM users WHERE first_seen LIKE ?", (f"{today}%",)).fetchone()[0]
        y_users = db.execute("SELECT COUNT(*) FROM users WHERE first_seen LIKE ?", (f"{yesterday}%",)).fetchone()[0]
        selected = db.execute("SELECT COUNT(*) FROM orders WHERE status='selected'").fetchone()[0]
        submitted = db.execute("SELECT COUNT(*) FROM orders WHERE status='submitted'").fetchone()[0]
        approved = db.execute("SELECT COUNT(*) FROM orders WHERE status='approved'").fetchone()[0]
        rejected = db.execute("SELECT COUNT(*) FROM orders WHERE status='rejected'").fetchone()[0]

    await update.message.reply_text(
        f"📊 BOT STATS\n\n"
        f"👥 TOTAL USERS : {total}\n"
        f"✅ ACTIVE USERS : {active}\n"
        f"🆕 NEW TODAY : {today_users}\n"
        f"📅 NEW YESTERDAY : {y_users}\n\n"
        f"🛒 SELECTED PACKAGE : {selected}\n"
        f"⏳ PENDING SCREENSHOTS : {submitted}\n"
        f"✅ APPROVED PAYMENTS : {approved}\n"
        f"❌ REJECTED PAYMENTS : {rejected}"
    )

async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    with db_connect() as db:
        rows = db.execute("SELECT user_id, first_name, username, last_seen FROM users ORDER BY last_seen DESC LIMIT 10").fetchall()
    if not rows:
        await update.message.reply_text("No users yet.")
        return
    text = "🆕 RECENT USERS\n"
    for r in rows:
        username = f"@{r['username']}" if r["username"] else "No username"
        text += f"\n👤 {r['first_name']} | {username}\n🆔 {r['user_id']}\n⏱ {r['last_seen']}\n"
    await update.message.reply_text(text)

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    with db_connect() as db:
        rows = db.execute("""
            SELECT o.order_id, o.user_id, o.package_key, o.screenshot_at, u.first_name, u.username
            FROM orders o LEFT JOIN users u ON u.user_id=o.user_id
            WHERE o.status='submitted'
            ORDER BY o.order_id DESC LIMIT 20
        """).fetchall()
    if not rows:
        await update.message.reply_text("✅ No pending payments.")
        return
    text = "⏳ PENDING PAYMENTS\n"
    for r in rows:
        username = f"@{r['username']}" if r["username"] else "No username"
        pkg = PACKAGES.get(r["package_key"], {}).get("name", r["package_key"])
        text += f"\n🧾 Order {r['order_id']}\n👤 {r['first_name']} | {username}\n🆔 {r['user_id']}\n📦 {pkg}\n⏱ {r['screenshot_at']}\n"
    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    msg = " ".join(context.args).strip()
    if not msg:
        await update.message.reply_text("Use: /broadcast Your message here")
        return

    with db_connect() as db:
        rows = db.execute("SELECT user_id FROM users WHERE is_active=1").fetchall()

    sent = failed = 0
    await update.message.reply_text(f"📢 Broadcast start: {len(rows)} active users")

    for r in rows:
        uid = r["user_id"]
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
            await asyncio.sleep(0.06)
        except RetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 1)
        except (Forbidden, BadRequest):
            failed += 1
            deactivate_user(uid)
        except Exception:
            failed += 1

    with db_connect() as db:
        db.execute("INSERT INTO broadcasts (message_text, created_at, sent_count, failed_count) VALUES (?, ?, ?, ?)", (msg, now_iso(), sent, failed))
        db.commit()

    await update.message.reply_text(f"✅ BROADCAST COMPLETE\n\nSent: {sent}\nFailed/Blocked: {failed}")

# ==========================================================
# MAIN
# ==========================================================
async def error_handler(update, context):
    logging.error("BOT ERROR", exc_info=context.error)

def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    if BOT_TOKEN == "YAHAN_APNA_BOT_TOKEN_DAAL":
        print("❌ Pehle BOT_TOKEN paste karo.")
        return

    init_database()
    save_demo_data()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    app.add_handler(CommandHandler("admin", admin_help))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", stats))
    app.add_handler(CommandHandler("recent", recent))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(CommandHandler("record_mms", record_mms))
    app.add_handler(CommandHandler("record_CHILD", record_CHILD))
    app.add_handler(CommandHandler("demo_status", demo_status))
    app.add_handler(CommandHandler("stop_recording", stop_recording))
    app.add_handler(CommandHandler("test_mms", test_mms))
    app.add_handler(CommandHandler("test_CHILD", test_CHILD))

    app.add_handler(CallbackQueryHandler(button_click))

    # Admin media = demo recording
    app.add_handler(
        MessageHandler(
            filters.User(ADMIN_ID) & (filters.PHOTO | filters.VIDEO | filters.Document.ALL),
            save_demo_media
        )
    )

    # User media = payment screenshot
    app.add_handler(
        MessageHandler(
            ~filters.User(ADMIN_ID) & (filters.PHOTO | filters.Document.IMAGE),
            screenshot_handler
        )
    )

    app.add_error_handler(error_handler)

    print("BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()