import telebot
from telebot import types
from config import BOT_TOKEN, AUTHORIZED_CHAT_IDS
from checker  check_card_full, luhn_check

bot = telebot.TeleBot(8920602452:AAEYAp8YNPp_bs-SkK27ifM0zVUz9QMel2k)

# ===== AUTH CHECK =====
def is_authorized(8811481879):
    return chat_id in AUTHORIZED_CHAT_IDS

# ===== /START =====
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    
    if not is_authorized(chat_id):
        bot.reply_to(message, "❌ You are not authorized to use this bot.")
        return
    
    welcome = """
🔥 <b>CC Checker Bot</b>

📌 <b>Single Check:</b>
<code>/check 4031633755589473|02|2028|387</code>

📌 <b>BIN Lookup:</b>
<code>/bin 403163</code>

📌 <b>Bulk Check:</b>
Send a .txt file with format:
<code>card|month|year|cvv</code>

📌 <b>Check Luhn:</b>
<code>/luhn 4031633755589473</code>

📌 <b>Your Chat ID:</b>
<code>{chat_id}</code>

⚠️ Only authorized users can use this bot.
"""
    bot.reply_to(message, welcome, parse_mode='HTML')

# ===== /CHECK =====
@bot.message_handler(commands=['check'])
def check_card_cmd(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id):
        bot.reply_to(message, "❌ Not authorized!")
        return
    
    text = message.text.replace("/check", "").strip()
    parts = text.split("|")
    
    if len(parts) != 4:
        bot.reply_to(message, "❌ Format: /check card|mm|yy|cvv")
        return
    
    card, month, year, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    
    if not luhn_check(card):
        bot.reply_to(message, "❌ Invalid Luhn!")
        return
    
    bot.reply_to(message, f"⏳ Checking {card[:4]}****{card[-4:]}...")
    
    result = check_card_full(card, month, year, cvv)
    response = format_result(result)
    bot.reply_to(message, response, parse_mode='HTML')

# ===== /BIN =====
@bot.message_handler(commands=['bin'])
def bin_cmd(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id):
        bot.reply_to(message, "❌ Not authorized!")
        return
    
    bin_num = message.text.replace("/bin", "").strip()
    if len(bin_num) < 6:
        bot.reply_to(message, "❌ Enter at least 6 digits!")
        return
    
    from checker import get_bin_info
    info = get_bin_info(bin_num[:6])
    
    if info:
        response = f"""
🔍 <b>BIN LOOKUP</b>

🔢 BIN: {bin_num}
🏦 Bank: {info['bank']}
🌍 Country: {info['country']}
💳 Brand: {info['brand']}
📋 Type: {info['type']}
"""
    else:
        response = "❌ BIN not found!"
    
    bot.reply_to(message, response, parse_mode='HTML')

# ===== /LUHN =====
@bot.message_handler(commands=['luhn'])
def luhn_cmd(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id):
        bot.reply_to(message, "❌ Not authorized!")
        return
    
    card = message.text.replace("/luhn", "").strip().replace(" ", "").replace("-", "")
    if not card.isdigit():
        bot.reply_to(message, "❌ Enter a valid card number!")
        return
    
    from checker import luhn_check
    valid = luhn_check(card)
    status = "✅ Valid" if valid else "❌ Invalid"
    bot.reply_to(message, f"🔢 Card: {card}\n📊 Luhn: {status}")

# ===== /CHATID =====
@bot.message_handler(commands=['chatid'])
def chatid_cmd(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"📌 Your Chat ID: <code>{chat_id}</code>", parse_mode='HTML')

# ===== BULK FILE =====
@bot.message_handler(content_types=['document'])
def handle_file(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id):
        bot.reply_to(message, "❌ Not authorized!")
        return
    
    file_info = bot.get_file(message.document.file_id)
    file = bot.download_file(file_info.file_path)
    content = file.decode('utf-8', errors='ignore')
    lines = content.strip().split('\n')
    
    bot.reply_to(message, f"⏳ Processing {len(lines)} cards...")
    
    results = []
    for line in lines:
        parts = line.strip().split("|")
        if len(parts) >= 4:
            card, month, year, cvv = parts[0], parts[1], parts[2], parts[3]
            if luhn_check(card):
                result = check_card_full(card, month, year, cvv)
                results.append(f"{card[:4]}****{card[-4:]}|{month}|{year}|{result['status']}")
            else:
                results.append(f"{card[:4]}****{card[-4:]}|{month}|{year}|INVALID")
    
    result_text = "\n".join(results)
    bot.send_document(message.chat.id, result_text.encode(), visible_file_name="results.txt")

# ===== FORMAT RESULT =====
def format_result(result):
    lines = []
    lines.append(f"💳 Card: {result['card'][:4]}****{result['card'][-4:]}")
    lines.append(f"📅 Exp: {result['month']}/{result['year']}")
    lines.append(f"🔑 CVV: {result['cvv']}")
    lines.append("")
    
    if result["bin_info"]:
        b = result["bin_info"]
        lines.append(f"🏦 Bank: {b['bank']}")
        lines.append(f"🌍 Country: {b['country']}")
        lines.append(f"💳 Brand: {b['brand']} - {b['type']}")
        lines.append("")
    
    status_emoji = {
        "LIVE": "✅",
        "DEAD": "❌",
        "INVALID": "⚠️",
        "UNKNOWN": "❓",
        "ERROR": "🚫"
    }
    
    lines.append(f"{status_emoji.get(result['status'], '❓')} Status: {result['status']}")
    lines.append(f"📝 {result['message']}")
    
    return "\n".join(lines)

# ===== RUN =====
if __name__ == "__main__":
    print("🤖 CC Checker Bot started!")
    print(f"👥 Authorized Chat IDs: {AUTHORIZED_CHAT_IDS}")
    bot.infinity_polling()