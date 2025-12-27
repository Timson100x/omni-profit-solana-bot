# 🚀 Omni Profit Solana Sniper Bot

**Professional Memecoin Trading Bot** mit MEV-Protection, 15s Aggressive Strategy und Auto-Staking.

## ⚡ Features

- **15-Second Signal Detection** - Aggressive DexScreener/GMGN.ai scanning
- **8-Check Validation System** - Liquidity, LP burned, mint revoked, holder distribution
- **MEV Protection** - Jito Bundle integration
- **Transaction Optimizer** - 8-12x faster trades (35ms RPC latency)
- **Auto rSOL Staking** - Trades werden direkt in rSOL investiert für passive Rewards
- **Helius Premium RPC** - Optimal performance und reliability

## 🎯 Quick Start

```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Configure .env.production
cp .env.production.TEMPLATE .env.production
# Edit: WALLET_PRIVATE_KEY, HELIUS_API_KEY, etc.

# 3. Start Production Bot
python run_advanced_bot.py
```

## 📊 System Status

- **Network**: Solana Mainnet via Helius
- **Signal Interval**: 15 seconds (aggressive)
- **Trade Size**: 0.05 - 0.1 SOL per signal
- **Daily Loss Limit**: 1.0 SOL
- **Auto-Staking**: rSOL (Renzo Restaked SOL)

## 🔒 Security

- Emergency Stop: Configurable via `.env`
- Slippage Protection: 5% max
- Price Impact Check: 10% max
- Daily Loss Limits enforced

## 📁 Structure

```
src/
├── blockchain/     # Solana RPC, Wallet, Transaction Optimizer
├── trading/        # Jupiter Swapper, Trade Manager
├── signals/        # Signal Processor, Validator
├── analysis/       # DexScreener, GMGN.ai clients
├── ai/            # Gemini AI agent
└── monitoring/    # Telegram/Discord notifications
```

## 🚀 Production Deployment

**Wichtig**: Deploy auf VPS (nicht Codespace) für Jupiter API access!

```bash
# VPS Setup
git clone https://github.com/foxyvega/omni-profit-solana-bot
cd omni-profit-solana-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Config
cp .env.production.TEMPLATE .env.production
# Edit .env.production

# Start
nohup python run_advanced_bot.py > bot.log 2>&1 &
```

## 💰 Wallet Management

- **Wallet Address**: H5qckhS57SA4g9NgeH9uSg6iaivpbtQyuXxD2KHwtETX
- **Minimum Balance**: 0.1 SOL (für Trades + Gas)
- **Auto-Staking**: Trades kaufen rSOL statt regular tokens für passive rewards

## 📈 Performance

- **Signal Detection**: 3 tokens per 15s loop
- **Validation Score**: 70-95/100 typical
- **Trade Execution**: 35ms RPC latency
- **Success Rate**: Depends on market conditions

---

**⚠️ Disclaimer**: Memecoin trading is highly risky. Use at your own risk.
