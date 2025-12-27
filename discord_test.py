#!/usr/bin/env python3
"""Discord Bot Test - Testet Discord Integration für Omni-Profit Bot"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_IDS = os.getenv('DISCORD_CHANNEL_IDS', '')

print("=" * 60)
print("🎮 DISCORD BOT TEST")
print("=" * 60)
print()

# Check Token
if not DISCORD_BOT_TOKEN:
    print("❌ DISCORD_BOT_TOKEN nicht in .env.production gesetzt!")
    print("   Füge hinzu: DISCORD_BOT_TOKEN=dein_token_hier")
    sys.exit(1)

print(f"✅ Bot Token: {DISCORD_BOT_TOKEN[:20]}...{DISCORD_BOT_TOKEN[-10:]}")

# Check Channel IDs
if not DISCORD_CHANNEL_IDS:
    print("⚠️  DISCORD_CHANNEL_IDS nicht gesetzt")
    print("   Tipp: Füge hinzu: DISCORD_CHANNEL_IDS=123456789012345678")
    print("   (Mehrere IDs mit Komma trennen)")
    print()
    print("   So findest du Channel IDs:")
    print("   1. Discord → Settings → Advanced → 'Developer Mode' aktivieren")
    print("   2. Rechtsklick auf Channel → 'Copy Channel ID'")
    print()

channel_ids = [cid.strip() for cid in DISCORD_CHANNEL_IDS.split(',') if cid.strip()]
if channel_ids:
    print(f"✅ Channel IDs: {', '.join(channel_ids)}")
print()

# Try to import discord.py
try:
    import discord
    from discord.ext import commands
    print("✅ discord.py installiert")
except ImportError:
    print("❌ discord.py nicht installiert!")
    print("   Installiere mit: pip install discord.py")
    sys.exit(1)

print()
print("🔄 Starte Discord Bot Test...")
print("-" * 60)

# Create bot with proper intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"\n✅ Bot verbunden als: {bot.user.name} (ID: {bot.user.id})")
    print(f"   In {len(bot.guilds)} Server(n)")
    print()
    
    for guild in bot.guilds:
        print(f"   📁 Server: {guild.name} (ID: {guild.id})")
        print(f"      Mitglieder: {guild.member_count}")
        print(f"      Channels: {len(guild.channels)}")
        print()
    
    # Test sending message to channels
    if channel_ids:
        print("📤 Sende Test-Nachrichten...")
        for channel_id in channel_ids:
            try:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    test_message = f"""🤖 **Omni-Profit Bot Test**

✅ Discord-Verbindung funktioniert!
🆔 Bot: {bot.user.name}
📊 Der Bot ist bereit, Trading-Signale zu überwachen!

🚀 Status: Aktiv im Monitoring-Mode
"""
                    await channel.send(test_message)
                    print(f"   ✅ Nachricht gesendet an: #{channel.name}")
                else:
                    print(f"   ❌ Channel {channel_id} nicht gefunden!")
                    print(f"      Stelle sicher dass:")
                    print(f"      - Der Bot zum Server eingeladen wurde")
                    print(f"      - Der Bot Zugriff auf diesen Channel hat")
            except discord.Forbidden:
                print(f"   ❌ Keine Berechtigung für Channel {channel_id}")
                print(f"      Bot braucht 'Send Messages' Permission!")
            except Exception as e:
                print(f"   ❌ Fehler bei Channel {channel_id}: {e}")
        print()
    else:
        print("⚠️  Keine Channel IDs zum Testen vorhanden")
        print()
    
    print("✅ Test abgeschlossen!")
    print("   Bot läuft jetzt und kann Nachrichten empfangen.")
    print("   Drücke CTRL+C zum Beenden")
    print()

@bot.event
async def on_message(message):
    # Ignore own messages
    if message.author == bot.user:
        return
    
    # Log messages in monitored channels
    if str(message.channel.id) in channel_ids:
        print(f"📨 Nachricht in #{message.channel.name}:")
        print(f"   Von: {message.author.name}")
        print(f"   Text: {message.content[:100]}")
        print()
    
    await bot.process_commands(message)

@bot.command(name='status')
async def status(ctx):
    """Bot Status Check"""
    await ctx.send(f"✅ Omni-Profit Bot läuft!\n🤖 Überwache {len(channel_ids)} Channel(s)")

# Run bot
try:
    print("🔌 Verbinde mit Discord...")
    bot.run(DISCORD_BOT_TOKEN)
except discord.LoginFailure:
    print("\n❌ Login fehlgeschlagen!")
    print("   Token ist ungültig oder abgelaufen")
    print("   Generiere neuen Token im Discord Developer Portal:")
    print("   https://discord.com/developers/applications")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n⛔ Bot gestoppt")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ Fehler: {e}")
    sys.exit(1)
