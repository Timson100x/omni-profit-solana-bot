#!/usr/bin/env python3
"""Test Telegram Bot Connection"""
import os
import sys
import requests

# Load from .env
from dotenv import load_dotenv
load_dotenv('.env.production')

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def test_telegram():
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN nicht gesetzt")
        return False
    
    if not CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID nicht gesetzt")
        return False
    
    print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
    print(f"✅ Chat ID: {CHAT_ID}")
    print()
    
    # Test Bot Info
    print("🔍 Teste Bot Info...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if data['ok']:
            bot_info = data['result']
            print(f"✅ Bot: @{bot_info['username']}")
            print(f"   Name: {bot_info['first_name']}")
            print()
        else:
            print(f"❌ Bot Info Fehler: {data}")
            return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False
    
    # Test Nachricht senden
    print("📤 Sende Test-Nachricht...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"""🤖 Omni-Profit Bot Test

✅ Telegram-Verbindung funktioniert!

👤 User: Tomi (@Bindaja37)
🆔 Chat ID: {CHAT_ID}
🤖 Bot aktiv und bereit für Benachrichtigungen!

📊 Der Bot kann jetzt:
- Trade-Benachrichtigungen senden
- Profit/Loss Updates schicken
- Notfall-Alerts verschicken

🚀 Bot-Status: Läuft im Simulation Mode
"""
    
    try:
        r = requests.post(url, json={
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        if data['ok']:
            print("✅ Test-Nachricht erfolgreich gesendet!")
            print("   Prüfe dein Telegram!")
            return True
        else:
            print(f"❌ Fehler beim Senden: {data}")
            return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

if __name__ == '__main__':
    success = test_telegram()
    sys.exit(0 if success else 1)
