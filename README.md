# 🚀 Omni-Profit Solana Trading Bot

**AI-powered memecoin trading system for Solana blockchain with multi-source signal aggregation.**

## ✨ Features

- **Multi-Source Signals**: Telegram, Discord, X (Twitter) monitoring
- **AI Analysis**: Google Gemini integration for token evaluation
- **DEX Integration**: Jupiter Aggregator for best swap prices
- **Risk Management**: Auto stop-loss, take-profit, position sizing
- **Real-time Data**: DexScreener API integration
- **Secure**: Encrypted wallet management

## 📁 Project Structure

```
src/
├── core/          # Config & Logging
├── blockchain/    # Solana RPC & Wallet
├── trading/       # Jupiter DEX & Trade Manager
├── signals/       # Signal Processing
├── ai/            # AI Agent (Gemini)
├── analysis/      # Market Data (DexScreener)
├── social/        # Discord & X Monitors  
└── telegram/      # Telegram Listener
```

## 🛠️ Setup

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.production.example` to `.env.production` and fill in your credentials:
```bash
WALLET_PRIVATE_KEY=<your_base58_key>
GEMINI_API_KEY=<your_key>
TELEGRAM_API_ID=<your_id>
```

### 3. Run
```bash
python main.py
```

## ⚠️ Security

- Never commit `.env.production`
- Use a separate wallet for bot trading
- Start with small position sizes

## 📊 Version

v1.0.0 - Initial Release (Dec 2025)

## 🧾 Latest changes (Devnet testing & safety)

- Added Devnet smoke tests and sign-only verification scripts (`scripts/devnet_e2e.py`, `scripts/sign_only_test.py`).
- Added robust Jupiter price helper with retries and tests (`src/trading/jupiter_client.py`).
- Added controlled Devnet transfer tool (`scripts/send_devnet_transfer.py`) — **disabled by default**; requires `ALLOW_REAL_TRANSACTIONS=true`.
- Integrated health check and CI workflow (`scripts/health_check.py`, `.github/workflows/health_check.yml`).
- Added notifier hooks for critical alerts (`src/monitoring/notifier.py`) and updated `PRODUCTION_CHECKLIST.md`.
- Small compatibility patch for `httpx` / `solana` provider to avoid runtime TypeErrors on some environments.

## 📄 License

MIT License - see LICENSE file
