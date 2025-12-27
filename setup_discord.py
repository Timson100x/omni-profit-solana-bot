#!/usr/bin/env python3
"""Discord Setup Assistant - Interaktive Konfiguration"""

import sys
sys.path.insert(0, '/workspaces/omni-profit-solana-bot')

print("=" * 70)
print("🤖 Discord Bot Setup Assistant")
print("=" * 70)
print()

print("Du brauchst 2 Dinge von Discord:")
print()
print("1️⃣  **Neuer Bot Token** (nach MFA Reset)")
print("2️⃣  **Channel ID** (aus deinem Server 'Foxy Vega')")
print()

# Schritt 1: Developer Mode
print("=" * 70)
print("📱 Schritt 1: Developer Mode aktivieren")
print("=" * 70)
print()
print("In Discord Desktop/Web:")
print("  → User Settings (Zahnrad unten links)")
print("  → Advanced (Erweitert)")
print("  → ✅ Developer Mode aktivieren")
print()
input("✅ Aktiviert? Drücke ENTER...")
print()

# Schritt 2: Channel ID
print("=" * 70)
print("🔍 Schritt 2: Channel ID kopieren")
print("=" * 70)
print()
print("In deinem Server 'Foxy Vega':")
print("  → Rechtsklick auf den Trading-Channel (z.B. #trading-bot)")
print("  → 'Copy Channel ID' klicken")
print("  → ID sieht aus wie: 1234567890123456789")
print()

channel_id = input("📋 Channel ID einfügen: ").strip()

while not channel_id or not channel_id.isdigit() or len(channel_id) < 17:
    print("❌ Ungültige Channel ID (muss 17-19 Ziffern sein)")
    channel_id = input("📋 Nochmal: ").strip()

print(f"✅ Channel ID: {channel_id}")
print()

# Schritt 3: Bot Token Reset
print("=" * 70)
print("🔐 Schritt 3: Bot Token zurücksetzen")
print("=" * 70)
print()
print("Öffne in Browser:")
print("  https://discord.com/developers/applications/1454133148546760846/bot")
print()
print("Dann:")
print("  1. Klick 'Reset Token' Button")
print("  2. Passwort + 2FA Code eingeben")
print("  3. Neuer Token wird angezeigt")
print("  4. Token kopieren (nur 1x sichtbar!)")
print()
print("⚠️  Token Format: MTQ1NDEzMzE0ODU0Njc2MDg0Ng.XXXXXX.YYYYYYY")
print()

bot_token = input("📋 Bot Token einfügen: ").strip()

while not bot_token or not bot_token.startswith("MTQ1"):
    print("❌ Ungültiger Token (muss mit MTQ5... beginnen)")
    bot_token = input("📋 Nochmal: ").strip()

print(f"✅ Token: {bot_token[:20]}...{bot_token[-10:]}")
print()

# Schritt 4: Message Content Intent
print("=" * 70)
print("⚙️  Schritt 4: Bot Permissions aktivieren")
print("=" * 70)
print()
print("Noch in Developer Portal:")
print("  → Bot Tab (links)")
print("  → Unter 'Privileged Gateway Intents':")
print("     ☑️  MESSAGE CONTENT INTENT aktivieren")
print("     ☑️  SERVER MEMBERS INTENT aktivieren")
print("  → 'Save Changes' klicken")
print()
input("✅ Gespeichert? Drücke ENTER...")
print()

# Generiere .env
print("=" * 70)
print("📝 Deine .env.production Konfiguration")
print("=" * 70)
print()
print("# Discord Bot Configuration")
print(f"DISCORD_BOT_TOKEN={bot_token}")
print(f"DISCORD_CHANNEL_IDS={channel_id}")
print()

# Schreibe zu File
try:
    from dotenv import load_dotenv
    import os
    
    load_dotenv('.env.production')
    
    # Lese existierende .env
    with open('.env.production', 'r') as f:
        lines = f.readlines()
    
    # Update Discord Werte
    updated = False
    token_updated = False
    
    with open('.env.production', 'w') as f:
        for line in lines:
            if line.startswith('DISCORD_BOT_TOKEN='):
                f.write(f'DISCORD_BOT_TOKEN={bot_token}\n')
                token_updated = True
            elif line.startswith('DISCORD_CHANNEL_IDS='):
                f.write(f'DISCORD_CHANNEL_IDS={channel_id}\n')
                updated = True
            else:
                f.write(line)
        
        # Füge hinzu falls nicht vorhanden
        if not token_updated:
            f.write(f'\nDISCORD_BOT_TOKEN={bot_token}\n')
        if not updated:
            f.write(f'DISCORD_CHANNEL_IDS={channel_id}\n')
    
    print("✅ .env.production wurde aktualisiert!")
    print()

except Exception as e:
    print(f"⚠️  Konnte .env nicht automatisch updaten: {e}")
    print("   Füge die Zeilen manuell hinzu")
    print()

# Test Command
print("=" * 70)
print("🧪 Bot testen")
print("=" * 70)
print()
print("Führe aus:")
print()
print("  python discord_test.py")
print()
print("Expected Output:")
print("  ✅ Logged in as: Dein Bot#1234")
print("  ✅ Guilds: ['Foxy Vega']")
print("  ✅ Test message sent to channel")
print()

print("=" * 70)
print("🎉 Setup abgeschlossen!")
print("=" * 70)
print()
print("Nächste Schritte:")
print("  1. python discord_test.py")
print("  2. Bot läuft → Siehe Nachrichten in Discord")
print("  3. Integriere in complete_system.py")
