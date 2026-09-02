import telebot
from telebot import types
import time, datetime

# ==========================================
# 🛑 DETAILS (Aapki Details set kar di hain)
# ==========================================
BOT_TOKEN = "8293793841:AAFrKiukw_OqwXzGsFf4ZAI2jSfPEAdobro" 
OWNER_ID = 7774294727  # <-- Screenshot se aapki ID daal di hai
OWNER_USERNAME = "@REAL_JOY_99" # <-- Naya Owner Username
BOT_NAME = "JOY WEBS" # <-- Bot ka Naam

CHANNEL_1 = "https://t.me/+O_Q5wllImjw3NTRl"
CHANNEL_2 = "https://t.me/joy_webs"
CHANNEL_3 = "https://t.me/+LQ787BPSnFYxOWY1"

FSUB_CHANNELS = ["O_Q5wllImjw3NTRl", "joy_webs", "LQ787BPSnFYxOWY1"] 

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 🔒 FORCE SUBSCRIBE SYSTEM
# ==========================================
def is_subscribed(user_id):
    for channel in FSUB_CHANNELS:
        try:
            chat_member = bot.get_chat_member(f"@{channel}", user_id)
            if chat_member.status == 'left' or chat_member.status == 'kicked':
                return False
        except:
            pass
    return True

def check_subscription(message):
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("📢 Channel 1 (JOIN)", url=CHANNEL_1)
        btn2 = types.InlineKeyboardButton("📢 Channel 2 (JOIN)", url=CHANNEL_2)
        btn3 = types.InlineKeyboardButton("📢 Channel 3 (JOIN)", url=CHANNEL_3)
        btn_verify = types.InlineKeyboardButton("✅ Main Join Ho Gaya", callback_data="verify")
        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        markup.add(btn_verify)
        
        bot.reply_to(message, 
            f"⚠️ *WELCOME TO {BOT_NAME}*\n\n"
            "Bot use karne ke liye pehle hamare saare channels join karein!\n"
            "Neeche buttons dabayein aur phir '✅ Main Join Ho Gaya' par click karein.", 
            parse_mode='Markdown', reply_markup=markup)
        return False
    return True

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    if check_subscription(call.message):
        bot.answer_callback_query(call.id, "✅ Verified! Ab aap bot use kar sakte hain.")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✅ *Verified! Ab aap saare commands use kar sakte hain!*", parse_mode='Markdown')
    else:
        bot.answer_callback_query(call.id, "❌ Abhi bhi koi channel join nahi kiya!", show_alert=True)

# ==========================================
# ⚡ COMMANDS
# ==========================================

# 1. START COMMAND (Mukhya Command)
@bot.message_handler(commands=['start'])
def start_command(message):
    if not check_subscription(message): return
    markup = types.InlineKeyboardMarkup()
    # Buttons add kiye hain
    btn_id = types.InlineKeyboardButton("🆔 Mera ID Lo", callback_data="get_id")
    btn_owner = types.InlineKeyboardButton(f"👑 {OWNER_USERNAME}", url=f"tg://user?id={OWNER_ID}")
    btn_channel = types.InlineKeyboardButton("📢 Channel Join Karo", url=CHANNEL_2)
    markup.add(btn_id, btn_owner)
    markup.add(btn_channel)
    
    # Image ke saath Start Message
    photo_url = "https://i.ibb.co/3k7x5Qx/joywebs.jpg" # Aap yahan apni photo ka direct link daal sakte hain
    caption = (f"🔥 *WELCOME TO {BOT_NAME}* 🔥\n\n"
               "🔰 *YE HAI HUMARA STORE*\n\n"
               f"👑 *OWNER:* {OWNER_USERNAME}\n"
               "🛒 *Yahan sabse best deals milti hain!*\n\n"
               "Neeche diye buttons se commands use karein 👇")
    
    try:
        bot.send_photo(message.chat.id, photo_url, caption=caption, parse_mode='Markdown', reply_markup=markup)
    except:
        # Agar photo fail ho jaye toh text bhej dega
        bot.reply_to(message, caption, parse_mode='Markdown', reply_markup=markup)

# 2. ID COMMAND
@bot.message_handler(commands=['id'])
def get_id(message):
    if not check_subscription(message): return
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name
    
    text = (f"📛 *Naam:* {name}\n"
            f"🆔 *User ID:* `{user_id}`\n"
            f"💬 *Chat ID:* `{chat_id}`")
            
    if message.reply_to_message:
        rep_id = message.reply_to_message.from_user.id
        rep_name = message.reply_to_message.from_user.first_name
        text += f"\n\n🎯 *Reply Kiya:* {rep_name}\n🆔 *Unki ID:* `{rep_id}`"
        
    bot.reply_to(message, text, parse_mode='Markdown')

# ID Button Handler
@bot.callback_query_handler(func=lambda call: call.data == "get_id")
def get_id_button(call):
    user_id = call.from_user.id
    name = call.from_user.first_name
    bot.answer_callback_query(call.id, "ID Nikal rahe hain...")
    bot.send_message(call.message.chat.id, f"📛 *Naam:* {name}\n🆔 *User ID:* `{user_id}`", parse_mode='Markdown')

# 3. HELP
@bot.message_handler(commands=['help'])
def help_command(message):
    if not check_subscription(message): return
    help_text = (f"🛠 *{BOT_NAME} Commands:*\n\n"
                 "/start - Bot shuru karein\n"
                 "/id - Apni User ID aur Chat ID\n"
                 "/help - Ye menu\n"
                 "/owner - Owner details\n"
                 "/channel - Channels ke links\n"
                 "/ping - Bot ki speed\n"
                 "/time - Current time\n"
                 "/about - Bot ke baare mein\n"
                 "/rules - Rules padhein")
    bot.reply_to(message, help_text, parse_mode='Markdown')

# 4. OWNER
@bot.message_handler(commands=['owner'])
def owner_command(message):
    if not check_subscription(message): return
    bot.reply_to(message, f"👑 *YE HAI OWNER:*\n\n{OWNER_USERNAME}\n\n[Contact Owner](tg://user?id={OWNER_ID})", parse_mode='Markdown')

# 5. CHANNEL
@bot.message_handler(commands=['channel'])
def channel_command(message):
    if not check_subscription(message): return
    bot.reply_to(message, f"📢 *HUMARE CHANNELS JOIN KARO:*\n\n[Channel 1]({CHANNEL_1})\n[Channel 2]({CHANNEL_2})\n[Channel 3]({CHANNEL_3})", parse_mode='Markdown')

# 6. PING
@bot.message_handler(commands=['ping'])
def ping_command(message):
    if not check_subscription(message): return
    start = time.time()
    msg = bot.reply_to(message, "🏓 Pinging...")
    end = time.time()
    ms = round((end - start) * 1000)
    bot.edit_message_text(f"⚡️ *PONG!*\n\nSpeed: `{ms}ms`", chat_id=message.chat.id, message_id=msg.message_id, parse_mode='Markdown')

# 7. TIME
@bot.message_handler(commands=['time'])
def time_command(message):
    if not check_subscription(message): return
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(message, f"⏰ *Current Time:*\n`{now}`", parse_mode='Markdown')

# 8. ABOUT
@bot.message_handler(commands=['about'])
def about_command(message):
    if not check_subscription(message): return
    bot.reply_to(message, f"🤖 *{BOT_NAME} BOT v3.0*\n\nYeh bot 100% secure aur advanced hai.\n\nDeveloper: {OWNER_USERNAME}", parse_mode='Markdown')

# 9. RULES
@bot.message_handler(commands=['rules'])
def rules_command(message):
    if not check_subscription(message): return
    bot.reply_to(message, f"📜 *{BOT_NAME} RULES:*\n\n"
                          "1. Har command se pehle channels join karein.\n"
                          "2. Kisi ko abuse na karein.\n"
                          "3. Bot ko spam na karein.\n"
                          "4. Owner ko respect karein.\n\n"
                          f"👑 {OWNER_USERNAME}", parse_mode='Markdown')

# ==========================================
# 🚀 BOT START
# ==========================================
if __name__ == '__main__':
    print(f"{BOT_NAME} Bot is Running...")
    bot.infinity_polling()