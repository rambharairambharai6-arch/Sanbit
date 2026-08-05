import requests
import re
import time

# ===== STRIPE CHECKER =====
def check_card(card, month, year, cvv):
    """
    Check card via Stripe API
    Returns: (status, message)
    """
    
    # Stripe API endpoints
    token_url = "https://api.stripe.com/v1/tokens"
    charge_url = "https://api.stripe.com/v1/payment_intents"
    
    # Replace with your Stripe secret key
    STRIPE_SECRET = "sk_live_XXXXXXXXXXXXXXXXXXXXXXXX"
    
    headers = {
        "Authorization": f"Bearer {STRIPE_SECRET}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"
    }
    
    try:
        # Step 1: Create token
        token_data = {
            "card[number]": card,
            "card[exp_month]": month,
            "card[exp_year]": year,
            "card[cvc]": cvv
        }
        
        token_res = requests.post(token_url, data=token_data, headers=headers, timeout=10)
        
        if token_res.status_code != 200:
            return "DEAD", f"Token failed: {token_res.status_code}"
        
        token = token_res.json().get("id")
        if not token:
            return "DEAD", "No token received"
        
        # Step 2: Create payment intent
        charge_data = {
            "amount": 100,  # $1 test charge
            "currency": "usd",
            "payment_method_data[type]": "card",
            "payment_method_data[card][token]": token,
            "confirm": "true"
        }
        
        charge_res = requests.post(charge_url, data=charge_data, headers=headers, timeout=10)
        
        if charge_res.status_code == 200:
            status = charge_res.json().get("status", "unknown")
            if status == "succeeded":
                return "LIVE", "✅ Charged successfully!"
            elif status == "requires_capture":
                return "LIVE", "✅ Hold placed!"
            else:
                return "UNKNOWN", f"Status: {status}"
        
        # Check error messages
        error_text = charge_res.text.lower()
        if "insufficient_funds" in error_text:
            return "LIVE", "💰 Insufficient funds (Live card)"
        elif "declined" in error_text:
            return "DEAD", "❌ Declined"
        elif "card_error" in error_text:
            return "DEAD", "❌ Card error"
        elif "fraudulent" in error_text:
            return "DEAD", "❌ Fraudulent"
        elif "expired_card" in error_text:
            return "DEAD", "❌ Card expired"
        elif "incorrect_cvc" in error_text:
            return "LIVE", "⚠️ Incorrect CVV (Card is live)"
        else:
            return "UNKNOWN", f"⚠️ Unknown: {charge_res.status_code}"
            
    except Exception as e:
        return "ERROR", f"❌ Error: {str(e)[:50]}"

# ===== LUHN VALIDATION =====
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

# ===== BIN LOOKUP =====
def get_bin_info(bin_num):
    try:
        url = f"https://lookup.binlist.net/{bin_num}"
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

# ===== MAIN CHECK FUNCTION =====
def check_card_full(card, month, year, cvv):
    result = {
        "card": card,
        "month": month,
        "year": year,
        "cvv": cvv,
        "luhn": False,
        "status": "UNKNOWN",
        "message": "",
        "bin_info": None
    }
    
    # Luhn check
    if not luhn_check(card):
        result["status"] = "INVALID"
        result["message"] = "❌ Invalid Luhn"
        return result
    
    result["luhn"] = True
    
    # BIN info
    bin_info = get_bin_info(card[:6])
    if bin_info:
        result["bin_info"] = bin_info
    
    # Stripe check
    status, message = check_card(card, month, year, cvv)
    result["status"] = status
    result["message"] = message
    
    return result

# ===== FORMAT OUTPUT =====
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
    lines.append(f"📝 Message: {result['message']}")
    
    return "\n".join(lines)

# ===== USAGE =====
if __name__ == "__main__":
    # Single check
    card = "4031633755589473"
    month = "02"
    year = "2028"
    cvv = "387"
    
    result = check_card_full(card, month, year, cvv)
    print(format_result(result))
    
    # Bulk from file
    # cards = [
    #     ("4111111111111111", "12", "2026", "123"),
    #     ("5555555555554444", "12", "2026", "123"),
    # ]
    # for c, m, y, cv in cards:
    #     r = check_card_full(c, m, y, cv)
    #     print(format_result(r))