# 🚀 Auto-Stake Guide: Automatischer SOL → Staking Token Swap

## Übersicht

Der **Auto-Stake Service** konvertiert automatisch deine SOL zu Liquid Staking Tokens über **Jupiter Aggregator**, um passives Einkommen zu generieren während du tradest.

## 🌊 Verfügbare Staking Tokens

| Token | Anbieter | APY | TVL | Liquidität |
|-------|----------|-----|-----|------------|
| **jitoSOL** | Jito | 7.5% | $2.8B | ⭐⭐⭐ Beste |
| **mSOL** | Marinade | 7.0% | $1.2B | ⭐⭐⭐ Beste |
| **bSOL** | BlazeStake | 6.8% | $150M | ⭐⭐ Gut |
| **rSOL** | Raydium | 6.5% | $400M | ⭐⭐ Gut |
| **stSOL** | Lido | 6.2% | $500M | ⭐⭐ Gut |

**Empfehlung:** jitoSOL oder mSOL (höchste APY + Liquidität)

## 🔧 Installation

```bash
# Bereits installiert in deinem Bot
pip install aiohttp solana solders
```

## 💻 Verwendung

### Option 1: Python Script

```python
import asyncio
from src.trading.auto_stake_swap import AutoStakeSwap

async def stake_sol():
    async with AutoStakeSwap() as swapper:
        # 90% deiner SOL zu jitoSOL konvertieren
        result = await swapper.auto_stake(
            target_token="jitoSOL",  # oder "mSOL", "rSOL", "bSOL"
            percentage=90.0,          # 90% staken
            min_reserve_sol=0.02,     # 0.02 SOL Reserve für Gas
            simulate_only=True,       # False für echten Swap
        )
        
        if result.success:
            print(f"✅ Getauscht: {result.input_amount} SOL → {result.output_amount} jitoSOL")
        else:
            print(f"❌ Fehler: {result.error}")

asyncio.run(stake_sol())
```

### Option 2: Command Line

```bash
cd /workspaces/omni-profit-solana-bot
.venv/bin/python src/trading/auto_stake_swap.py
```

## 🎯 Features

### 1. Automatische Balance-Prüfung
- Prüft SOL Balance vor Swap
- Reserviert automatisch SOL für Gas Fees
- Verhindert zu kleine Swaps

### 2. Jupiter Integration
- Beste Preise durch Route-Aggregation
- Slippage Protection (0.5% default)
- Price Impact Warnung bei >2%

### 3. Multi-Token Support
```python
# Beispiele
await swapper.auto_stake(target_token="jitoSOL")  # Höchste APY
await swapper.auto_stake(target_token="mSOL")     # Beste Liquidität
await swapper.auto_stake(target_token="rSOL")     # Raydium
await swapper.auto_stake(target_token="bSOL")     # BlazeStake
```

### 4. Sicherheits-Features
- **Simulation Mode**: Teste ohne echte Transaktion
- **Reserve Protection**: Behält immer SOL für Gas
- **Price Impact Check**: Warnt bei hohem Slippage
- **Quote Validation**: Prüft Jupiter Quote vor Swap

## 📊 Beispiel-Session

```bash
$ python src/trading/auto_stake_swap.py

======================================================================
🚀 Auto-Stake Swap - Jupiter Integration
======================================================================

💰 Aktuelle Balance: 0.176040 SOL

📊 Verfügbare Staking Tokens:
   1. mSOL (Marinade)   - 7.0% APY
   2. rSOL (Raydium)    - 6.5% APY
   3. jitoSOL (Jito)    - 7.5% APY
   4. bSOL (BlazeStake) - 6.8% APY

🔄 Demo: SOL → mSOL

✅ Swap erfolgreich (Simulation)
   Input:  0.140436 SOL
   Output: 0.139821 mSOL
   Rate:   0.9956
```

## 🔄 Bot Integration

Füge Auto-Stake zu deinem Trading Bot hinzu:

```python
# In complete_system.py

from src.trading.auto_stake_swap import AutoStakeSwap

async def initialize_auto_stake():
    """Stake SOL beim Bot-Start."""
    async with AutoStakeSwap() as swapper:
        balance = await swapper.get_sol_balance()
        
        # Nur staken wenn genug SOL vorhanden
        if balance > 0.1:
            result = await swapper.auto_stake(
                target_token="jitoSOL",
                percentage=85.0,  # Konservativ: 85%
                simulate_only=False,  # Echter Swap
            )
            
            if result.success:
                logger.info(f"Auto-staked {result.input_amount} SOL")

# Beim Bot-Start ausführen
await initialize_auto_stake()
```

## ⚙️ Konfiguration

In `.env.production`:

```bash
# Bereits konfiguriert
WALLET_PRIVATE_KEY=your_key_here
RPC_URL=https://api.mainnet-beta.solana.com

# Sicherheit
ALLOW_REAL_TRANSACTIONS=false  # Auf true setzen für echte Swaps
```

## 💰 ROI Berechnung

### Deine aktuelle Balance: 0.176 SOL

| Szenario | Stake Amount | Nach 1 Jahr | Gewinn |
|----------|--------------|-------------|--------|
| **Ohne Staking** | 0 SOL | 0.176 SOL | 0 SOL |
| **90% → mSOL** | 0.158 SOL | 0.169 SOL | +0.011 SOL |
| **90% → jitoSOL** | 0.158 SOL | 0.170 SOL | +0.012 SOL |

**Mit Trading (20% Profit):**
- Ohne Staking: 0.211 SOL (+20%)
- Mit jitoSOL: 0.229 SOL (+20% Trading + 7.5% Staking = **+30.1%**)

## 🚨 Wichtige Hinweise

### Vor dem ersten Swap:

1. **Teste im Simulation Mode:**
   ```python
   simulate_only=True  # Immer zuerst testen!
   ```

2. **Prüfe Jupiter Status:**
   ```bash
   curl https://quote-api.jup.ag/v6/quote
   ```

3. **Gas Reserve:**
   - Minimum 0.02 SOL behalten
   - Empfohlen 0.05 SOL für viele Transaktionen

4. **Price Impact:**
   - <1%: ✅ Gut
   - 1-2%: ⚠️ OK
   - >2%: ❌ Zu viel, kleinere Menge verwenden

### Risiken:

- **Slippage**: Preis kann sich während Transaktion ändern
- **Network Congestion**: Hohe Gas Fees bei Traffic
- **Smart Contract Risk**: Staking Protocol Bugs (sehr selten)
- **Depeg Risk**: Token könnte von SOL abweichen (historisch <0.1%)

## 🔍 Monitoring

Check deine Staking Token Balance:

```python
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

async def check_msol_balance():
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    
    # Token Account abfragen
    response = await client.get_token_accounts_by_owner(
        your_wallet_pubkey,
        {"mint": Pubkey.from_string("mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So")}
    )
    
    # Balance anzeigen
    for account in response.value:
        print(f"mSOL Balance: {account.account.data.parsed['info']['tokenAmount']['uiAmount']}")
```

## 🆘 Troubleshooting

### "Jupiter API unreachable"
```bash
# Prüfe Internet-Verbindung
curl https://quote-api.jup.ag/v6/quote

# Verwende alternativen RPC
export RPC_URL=https://solana-api.projectserum.com
```

### "Balance too low"
- Du brauchst minimum 0.05 SOL (0.02 Gas + 0.03 Swap)
- Lade mehr SOL auf dein Wallet

### "High price impact"
- Reduziere Swap Amount: `percentage=50.0` statt 90%
- Oder verwende Token mit höherer Liquidität (jitoSOL, mSOL)

## 📚 Weiterführende Links

- Jupiter Docs: https://docs.jup.ag
- Marinade: https://marinade.finance
- Jito: https://www.jito.network
- Raydium: https://raydium.io

## 🎉 Quick Start

```bash
# 1. Test im Simulation Mode
python src/trading/auto_stake_swap.py

# 2. Wenn alles OK: Echter Swap
# Setze in .env.production:
ALLOW_REAL_TRANSACTIONS=true

# 3. Führe aus
python src/trading/auto_stake_swap.py

# 4. Prüfe Balance auf Solscan
# https://solscan.io/account/YOUR_WALLET_ADDRESS
```

**Los geht's! 🚀**
