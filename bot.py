import telebot
import requests
import time
import threading
import os
import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔥 BOT TOKEN - APNA TOKEN DAALO
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# 🔥 OWNER INFO
OWNER_USERNAME = "@JOYxWEB"
OWNER_NAME = "JOY WEB"
WELCOME_TEXT = "WELCOME TO JOY WEB"

# 🔥 CHANNEL LINKS (FORCE SUBSCRIBE)
CHANNELS = [
    {"link": "https://t.me/+O_Q5wllImjw3NTRl", "id": "@join_joy_web1"},
    {"link": "https://t.me/joy_webs", "id": "@joy_webs"},
    {"link": "https://t.me/+LQ787BPSnFYxOWY1", "id": "@join_joy_web3"}
]

# BOT INIT
bot = telebot.TeleBot(BOT_TOKEN)

# 🛡️ STORE USER DATA (TEMP)
user_data = {}

# ✅ CHECK IF USER JOINED ALL CHANNELS
def is_user_joined(user_id):
    try:
        for channel in CHANNELS:
            chat_id = channel['id']
            try:
                member = bot.get_chat_member(chat_id, user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except:
                # Agar channel ID nahi milti toh link se try karo
                try:
                    chat_info = bot.get_chat(chat_id)
                    member = bot.get_chat_member(chat_info.id, user_id)
                    if member.status in ['left', 'kicked']:
                        return False
                except:
                    return False
        return True
    except:
        return False

# 📋 FORCE SUBSCRIBE KEYBOARD
def force_sub_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, channel in enumerate(CHANNELS):
        btn = InlineKeyboardButton(
            text=f"📢 JOIN CHANNEL {i+1}",
            url=channel['link']
        )
        keyboard.add(btn)
    
    btn_check = InlineKeyboardButton(
        text="✅ CHECK SUBSCRIPTION",
        callback_data="check_sub"
    )
    keyboard.add(btn_check)
    
    btn_owner = InlineKeyboardButton(
        text=f"👑 {OWNER_NAME}",
        url="https://t.me/JOYxWEB"
    )
    keyboard.add(btn_owner)
    
    return keyboard

# 🚀 MAIN START COMMAND
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    
    if is_user_joined(user_id):
        # ✅ USER JOINED ALL CHANNELS
        welcome = f"""
╔══════════════════════════╗
║  🎉 {WELCOME_TEXT} 🎉  ║
╠══════════════════════════╣
║  👑 OWNER: {OWNER_USERNAME}  ║
║  📢 CHANNEL: @joy_webs     ║
║  💬 GROUP: @joy_web_group  ║
╚══════════════════════════╝

✅ Aap sabhi channels mein join ho chuke hain!

🔥 AB AAP BOT USE KAR SAKTE HAIN
💡 Koi bhi command bhejo

⚠️ Agar bot kaam na kare toh owner se contact karein
        """
        bot.reply_to(message, welcome, parse_mode='HTML')
    else:
        # ❌ USER NOT JOINED
        msg = f"""
╔══════════════════════════╗
║  🚫 FORCE SUBSCRIBE 🚫   ║
╠══════════════════════════╣
║  {WELCOME_TEXT}  ║
║  👑 {OWNER_USERNAME}     ║
╚══════════════════════════╝

❌ <b>AAP NE SABHI CHANNELS JOIN NAHI KIE!</b>

📢 <b>NICHE DIYE GAYE SABHI CHANNELS JOIN KAREN:</b>

⚠️ <b>JAB TAK AAP SABHI CHANNELS MEIN JOIN NAHI HOGE
TAB TAK BOT KAAM NAHI KAREGA!</b>

👇 <b>NEECHE BUTTONS DABAYEIN AUR JOIN KAREIN</b>
        """
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=force_sub_keyboard())

# ✅ CHECK SUBSCRIPTION CALLBACK
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    msg_id = call.message.message_id
    chat_id = call.message.chat.id
    
    if is_user_joined(user_id):
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"""
✅ <b>SUBSCRIBED SUCCESSFULLY!</b>

🎉 Aap sabhi channels mein join ho chuke hain!

🔥 AB AAP BOT USE KAR SAKTE HAIN
💡 /start dobara dabayein

👑 {OWNER_NAME}
            """,
            parse_mode='HTML'
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Aap abhi bhi sabhi channels mein join nahi hain!",
            show_alert=True
        )

# 🛡️ PROTECT ALL COMMANDS - AGAR JOIN NAHI TO BLOCK
@bot.message_handler(func=lambda message: True)
def protect_all_commands(message):
    user_id = message.from_user.id
    
    # CHECK SUBSCRIPTION
    if not is_user_joined(user_id):
        msg = f"""
╔══════════════════════════╗
║  🚫 ACCESS DENIED 🚫     ║
╠══════════════════════════╣
║  {WELCOME_TEXT}  ║
║  👑 {OWNER_USERNAME}     ║
╚══════════════════════════╝

❌ <b>AAP NE SABHI CHANNELS JOIN NAHI KIE!</b>

📢 <b>NICHE DIYE GAYE SABHI CHANNELS JOIN KAREN:</b>

⚠️ <b>JAB TAK AAP SABHI CHANNELS MEIN JOIN NAHI HOGE
TAB TAK KOI COMMAND KAAM NAHI KAREGA!</b>

👇 <b>NEECHE BUTTONS DABAYEIN AUR JOIN KAREIN</b>
        """
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=force_sub_keyboard())
        return
    
    # 🎯 AGAR USER JOINED HAI TO YAHAN SE AAGE BADHO
    # APNA MAIN BOT LOGIC YAHAN LIKHO
    
    # EXAMPLE: ECHO COMMAND
    if message.text.startswith('/'):
        bot.reply_to(message, f"✅ Command received: {message.text}\n\n🔥 Aap fully verified hain!")
    else:
        bot.reply_to(message, f"✅ {message.from_user.first_name}, aapka message mil gaya!\n\n💡 Koi bhi command bhej sakte hain.")

# 💀 KILL SWITCH - EMERGENCY STOP (OWNER ONLY)
@bot.message_handler(commands=['kill'])
def kill_bot(message):
    if message.from_user.username == "JOYxWEB":
        bot.reply_to(message, "💀 BOT SHUTTING DOWN...")
        os._exit(0)
    else:
        bot.reply_to(message, "❌ Sirf owner ko ye command use karne ki permission hai!")

# 🔥 BROADCAST (OWNER ONLY)
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.username != "JOYxWEB":
        bot.reply_to(message, "❌ Sirf owner ko ye command use karne ki permission hai!")
        return
    
    # BROADCAST LOGIC YAHAN
    bot.reply_to(message, "📢 Broadcast feature activated!")

# ⚡ START BOT
print("🔥 BOT STARTED SUCCESSFULLY!")
print(f"👑 OWNER: {OWNER_USERNAME}")
print(f"📢 CHANNELS: {len(CHANNELS)} channels force subscribe")
print("✅ Bot is running...")

# POLLING START
bot.infinity_polling(timeout=10, long_polling_timeout=5)