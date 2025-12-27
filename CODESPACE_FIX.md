# 🔓 Codespace Blockade Umgehen

## Problem
GitHub Codespace blockiert externe DEX APIs:
- ❌ Jupiter API (`quote-api.jup.ag`) - HTTP 000
- ❌ Raydium API - Connection Timeout
- ✅ Helius RPC - Funktioniert!
- ✅ DexScreener API - Funktioniert!

## Lösung: On-Chain Swapper ✅

Statt externe APIs nutzen wir **direkte Solana Program Instructions** via Helius RPC:

### 3-Tier Fallback System

```
1. Jupiter API (extern) → Blockiert ❌
   ↓
2. On-Chain Swapper (Helius RPC) → Funktioniert! ✅
   ↓ 
3. Simulation Mode → Development ✅
```

### On-Chain Swapper Vorteile

✅ **Nutzt nur Helius RPC** (funktioniert in Codespace)
✅ **Keine externe API nötig** (Jupiter/Raydium nicht required)
✅ **Direkte Blockchain Interaktion** (Raydium Program Calls)
✅ **Volle Kontrolle** über Transactions
✅ **Funktioniert überall** wo Solana RPC verfügbar ist

### Implementierung

```python
from src.trading.onchain_swapper import onchain_swapper

# Direkter On-Chain Swap
success = await onchain_swapper.swap_sol_to_token(
    token_address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    amount_sol=0.1,
    slippage_bps=500
)
```

### Wie es funktioniert

1. **Pool Discovery via Helius RPC**
   - Query Raydium Program Accounts
   - Finde Pool für Token Pair
   - Cache für Performance

2. **Swap Calculation**
   - Berechne Output Amount (AMM Math: x*y=k)
   - Slippage Protection
   - Minimum Output Amount

3. **Transaction Building**
   - Erstelle Raydium Swap Instruction
   - Sign mit Wallet Keypair
   - Send via Helius RPC

4. **Confirmation**
   - Transaction Signature
   - Waiting for Confirmation
   - Balance Update

### Alternative: Deploy zu VPS

Falls On-Chain Swapper nicht ausreicht:

```bash
# Auf VPS/Server außerhalb Codespace:
git clone https://github.com/foxyvega/omni-profit-solana-bot
cd omni-profit-solana-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Config
cp .env.production.TEMPLATE .env.production
# Edit: API Keys

# Start
nohup python run_advanced_bot.py > live.log 2>&1 &
```

Auf VPS funktionieren **alle APIs** (Jupiter, Raydium, etc.)!

### Status Check

```bash
# Test API Connectivity
curl -s -m 3 https://quote-api.jup.ag/v6/quote
# 000 = Blockiert in Codespace
# 200/400 = Funktioniert auf VPS

# Test Helius RPC (sollte funktionieren)
curl -s https://mainnet.helius-rpc.com
```

## Zusammenfassung

✅ **On-Chain Swapper löst Codespace Problem**
✅ **Nutzt Helius RPC statt externe APIs**
✅ **Bot kann in Codespace traden**
✅ **Für maximale Performance: VPS Deployment**
