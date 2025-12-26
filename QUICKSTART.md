# 🚀 Omni-Profit Solana Bot - Quick Start

## ✅ Setup Complete!

Dein Bot ist **fertig konfiguriert** und ready to go!

### 📊 Aktueller Status
- ✅ Codespace läuft
- ✅ .env konfiguriert (Devnet)
- ✅ Gemini API Key gesetzt
- ✅ Solana Devnet RPCs aktiv
- ✅ Dependencies installiert

### 🔑 Konfigurierte Keys
```bash
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WS_URL=wss://api.devnet.solana.com
GEMINI_API_KEY=YOUR_GEMINI_KEY
```

## 🎯 Start Command

```bash
./start.sh
```

Oder manuell:
```bash
python complete_system.py
```

## 📝 Was fehlt noch?

### Required (für Trading):
- **WALLET_PRIVATE_KEY**: Dein Phantom Testnet Private Key (Base58)

### Optional (für Signals):
- TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
- DISCORD_BOT_TOKEN
- X_BEARER_TOKEN

## 🔧 Phantom Private Key exportieren

1. Öffne Phantom Extension
2. Settings → Show Secret Recovery Phrase / Export Private Key
3. Kopiere den **Base58 Private Key**
4. Füge in .env ein:
   ```bash
   WALLET_PRIVATE_KEY=dein_base58_key_hier
   ```

## 🧪 Test Mode

Der Bot ist auf **Devnet** konfiguriert:
- Deine 6 SOL sind Testnet-SOL
- Alle Trades laufen nur im Testnetz
- Kein echtes Geld involviert

## 🔄 Zum Mainnet wechseln

```bash
sed -i 's|devnet|mainnet-beta|g' .env
```

**⚠️ ACHTUNG**: Nur mit echtem SOL und echtem Wallet testen!

## 📊 Features

- 🤖 AI Token Analysis (Gemini)
- 📊 Multi-Source Signals (Telegram/Discord/X)
- 🔄 Jupiter DEX Integration

Quick devnet checks:

- `PYTHONPATH=. python scripts/sign_only_test.py` — sign-only verification (no broadcast)
- `ALLOW_REAL_TRANSACTIONS=true PYTHONPATH=. python scripts/send_devnet_transfer.py` — controlled small transfer on Devnet (uses wallet in `.env.production`)
- `PYTHONPATH=. python scripts/devnet_e2e.py` — end‑to‑end dry-run + simulation
- `PYTHONPATH=. python scripts/health_check.py` — health check (used by CI)

- 📈 Auto-Trading
- 🚨 Risk Management
- 📢 Telegram Bot Interface

## ❓ Probleme?

**Dependencies fehlen?**
```bash
pip install -r requirements.txt
```

**Gemini API Error?**
- Check API Key in .env
- Test: https://aistudio.google.com/app/api-keys

**Solana Connection Error?**
- Devnet RPC down? Wechsel zu: https://api.devnet.solana.com

