# Discord Integration - Omni-Profit Bot

## 📋 ENV Variablen

Der Bot nutzt diese Discord-Variablen aus `.env.production`:

```python
# In src/core/config.py
DISCORD_BOT_TOKEN: Optional[str] = None      # Bot Token vom Developer Portal
DISCORD_CHANNEL_IDS: Optional[str] = None    # Komma-separierte Channel IDs
```

## 🔍 Verwendung im Code

### 1. Signal Processor ([src/signals/processor.py](src/signals/processor.py))
```python
async def _collect_discord(self) -> List[Signal]:
    """Mock Discord signal collection"""
    # TODO: Implementiere echten Discord Listener mit discord.py
    # Liest aus DISCORD_CHANNEL_IDS konfigurierten Channels
    await asyncio.sleep(0.1)
    return []
```

### 2. Notifier ([src/monitoring/notifier.py](src/monitoring/notifier.py))
```python
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord(text: str) -> bool:
    if not DISCORD_WEBHOOK:
        log.info("discord_noop", reason="missing_webhook")
        return False
    try:
        r = requests.post(DISCORD_WEBHOOK, json={"content": text}, timeout=5)
        r.raise_for_status()
        log.info("discord_sent", text=text)
        return True
    except Exception as e:
        log.warning("discord_failed", error=str(e))
        return False
```

## 🚀 So aktivierst du Discord:

### 1. Developer Portal Setup
- Gehe zu https://discord.com/developers/applications
- Aktiviere "Message Content Intent" + "Server Members Intent"
- Bot zum Server einladen (OAuth2 URL Generator)

### 2. Channel IDs eintragen
```bash
# In .env.production
DISCORD_CHANNEL_IDS=123456789012345678,987654321098765432
```

### 3. Test ausführen
```bash
# Installiere discord.py
pip install discord.py

# Test
python discord_test.py
```

## ✅ Test erfolgreich wenn:
- Bot verbindet sich
- Zeigt alle Server
- Sendet Test-Nachricht in Channels
- Kann Nachrichten empfangen

## 🔧 Nächste Schritte:

Um Discord vollständig zu integrieren:
1. Implementiere echten Discord Client in `src/signals/processor.py`
2. Parsing-Logik für Trading-Signale aus Discord Messages
3. Webhook-Integration für Benachrichtigungen

Momentan ist Discord als Mock vorbereitet - der Test zeigt dass die Connection funktioniert!
