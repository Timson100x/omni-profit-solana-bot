#!/usr/bin/env python3
"""Discord Server Integration - Verbinde Bot mit deinem Server"""

import sys
sys.path.insert(0, '/workspaces/omni-profit-solana-bot')

INVITE_LINK = "https://discord.gg/zkwDJQdp"

print("=" * 70)
print("🔗 Discord Server Integration")
print("=" * 70)
print()

print(f"📱 Dein Discord Server: {INVITE_LINK}")
print()

# Step 1: Bot zum Server einladen
print("=" * 70)
print("Step 1: Bot zum Server einladen")
print("=" * 70)
print()
print("🤖 Dein Bot muss Member deines Servers sein!")
print()
print("OAuth2 URL generieren:")
print("  1. Gehe zu: https://discord.com/developers/applications/1454133148546760846/oauth2")
print("  2. URL Generator:")
print("     Scopes: ✅ bot, ✅ applications.commands")
print("     Bot Permissions:")
print("       ✅ Read Messages/View Channels")
print("       ✅ Send Messages")
print("       ✅ Read Message History")
print("       ✅ Add Reactions")
print()
print("  3. Copy Generated URL")
print("  4. Öffne URL im Browser")
print("  5. Wähle deinen Server aus Dropdown")
print("  6. 'Authorize' klicken")
print()

input("✅ Bot added to server? Press ENTER...")
print()

# Step 2: Trading Channel erstellen/finden
print("=" * 70)
print("Step 2: Trading Channel Setup")
print("=" * 70)
print()
print("Erstelle/finde einen Channel für Bot-Signale:")
print("  Empfohlener Name: #trading-signals oder #crypto-alerts")
print()
print("Channel Settings:")
print("  → Bot hat Read + Write Permissions")
print("  → Optional: Slow Mode (5-10 seconds) gegen Spam")
print()

channel_name = input("📝 Channel Name (z.B. trading-signals): ").strip() or "trading-signals"
print(f"✅ Channel: #{channel_name}")
print()

# Step 3: Channel ID kopieren
print("=" * 70)
print("Step 3: Channel ID")
print("=" * 70)
print()
print("Developer Mode aktiviert? (Settings → Advanced → Developer Mode)")
print()
print(f"Dann: Rechtsklick auf #{channel_name} → Copy Channel ID")
print()

channel_id = input("📋 Channel ID einfügen: ").strip()

while not channel_id or not channel_id.isdigit():
    print("❌ Ungültige ID")
    channel_id = input("📋 Nochmal: ").strip()

print(f"✅ Channel ID: {channel_id}")
print()

# Step 4: Bot Token
print("=" * 70)
print("Step 4: Bot Token")
print("=" * 70)
print()
print("Hole Bot Token aus Developer Portal:")
print("  https://discord.com/developers/applications/1454133148546760846/bot")
print()
print("Falls Token abgelaufen:")
print("  → 'Reset Token' Button")
print("  → MFA Code eingeben")
print("  → Neuen Token kopieren")
print()

bot_token = input("📋 Bot Token: ").strip()

while not bot_token or len(bot_token) < 50:
    print("❌ Token zu kurz")
    bot_token = input("📋 Nochmal: ").strip()

print(f"✅ Token: {bot_token[:30]}...")
print()

# Update .env
print("=" * 70)
print("📝 Update .env.production")
print("=" * 70)
print()

try:
    from dotenv import load_dotenv
    load_dotenv('.env.production')
    
    # Read existing
    with open('.env.production', 'r') as f:
        lines = f.readlines()
    
    # Update values
    updated_token = False
    updated_channel = False
    
    with open('.env.production', 'w') as f:
        for line in lines:
            if line.startswith('DISCORD_BOT_TOKEN='):
                f.write(f'DISCORD_BOT_TOKEN={bot_token}\n')
                updated_token = True
            elif line.startswith('DISCORD_CHANNEL_IDS='):
                f.write(f'DISCORD_CHANNEL_IDS={channel_id}\n')
                updated_channel = True
            else:
                f.write(line)
        
        # Add if missing
        if not updated_token:
            f.write(f'\nDISCORD_BOT_TOKEN={bot_token}\n')
        if not updated_channel:
            f.write(f'DISCORD_CHANNEL_IDS={channel_id}\n')
    
    print("✅ .env.production updated!")
    print()
    print("DISCORD_BOT_TOKEN=***")
    print(f"DISCORD_CHANNEL_IDS={channel_id}")

except Exception as e:
    print(f"⚠️  Error: {e}")
    print()
    print("Manual Update:")
    print(f"  DISCORD_BOT_TOKEN={bot_token}")
    print(f"  DISCORD_CHANNEL_IDS={channel_id}")

print()

# Test
print("=" * 70)
print("🧪 Test Bot Connection")
print("=" * 70)
print()
print("Run: python discord_test.py")
print()
print("Expected Output:")
print("  ✅ Logged in as: Omni Profit Bot")
print(f"  ✅ Found channel: #{channel_name}")
print("  ✅ Test message sent")
print()

# Advanced: Monitor Server
print("=" * 70)
print("🔥 Advanced: Monitor Server for Alpha")
print("=" * 70)
print()
print("Der Bot kann jetzt:")
print()
print("1. 📊 Token Calls monitoren")
print("   → Parsiert Nachrichten für Token Adressen")
print("   → Validiert mit Secrets (siehe secrets_advanced_trading.py)")
print("   → Auto-Trade wenn Signal gut")
print()
print("2. 💬 Community Sentiment")
print("   → Zählt mentions per Token")
print("   → High mentions = potential pump")
print()
print("3. 🚨 Alert System")
print("   → Sendet Profit/Loss updates")
print("   → Warnung bei großen Trades")
print()
print("Code Example:")
print("""
# In complete_system.py

async def monitor_discord_signals():
    client = discord.Client(intents=discord.Intents.all())
    
    @client.event
    async def on_message(message):
        if message.channel.id == TRADING_CHANNEL_ID:
            # Parse für Token Address
            token_addr = extract_token_address(message.content)
            
            if token_addr:
                # Validate mit Secrets
                is_safe = await validate_signal(token_addr)
                
                if is_safe:
                    # Execute Trade
                    await trade_manager.buy(token_addr, 0.1)
""")
print()

print("=" * 70)
print("🎉 Discord Integration Complete!")
print("=" * 70)
print()
print("Next Steps:")
print("  1. python discord_test.py  # Test connection")
print("  2. Monitor #{} for signals".format(channel_name))
print("  3. Implement auto-trading on signals")
print()
print(f"🔗 Join Server: {INVITE_LINK}")
