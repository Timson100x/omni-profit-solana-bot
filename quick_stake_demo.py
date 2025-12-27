#!/usr/bin/env python3
"""Quick Demo: Auto-Stake mit Jupiter"""

import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, '/workspaces/omni-profit-solana-bot')

from dotenv import load_dotenv
load_dotenv('.env.production')

print("=" * 70)
print("🚀 Jupiter Auto-Stake Demo")
print("=" * 70)
print()

# Token info
TOKENS = {
    "mSOL": {"name": "Marinade", "apy": 7.0, "tvl": "$1.2B"},
    "rSOL": {"name": "Raydium", "apy": 6.5, "tvl": "$400M"},
    "jitoSOL": {"name": "Jito", "apy": 7.5, "tvl": "$2.8B"},
    "bSOL": {"name": "BlazeStake", "apy": 6.8, "tvl": "$150M"},
}

print("📊 Verfügbare Staking Tokens via Jupiter:")
print()
for token, info in TOKENS.items():
    print(f"  {token:10s} | {info['name']:12s} | {info['apy']}% APY | TVL: {info['tvl']}")
print()

# Show usage
print("💡 Verwendung:")
print()
print("  from src.trading.auto_stake_swap import AutoStakeSwap")
print()
print("  async with AutoStakeSwap() as swapper:")
print("      result = await swapper.auto_stake(")
print("          target_token='jitoSOL',  # Beste APY")
print("          percentage=90.0,         # 90% deiner SOL")
print("          simulate_only=True,      # Test Mode")
print("      )")
print()

# Check balance
print("🔍 Prüfe Wallet Balance...")
print()

try:
    from src.blockchain.wallet import get_wallet
    from solana.rpc.api import Client
    
    wallet = get_wallet(os.getenv("WALLET_PRIVATE_KEY"))
    client = Client(os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))
    
    response = client.get_balance(wallet.pubkey())
    balance_sol = response.value / 1e9
    
    print(f"💰 Wallet: {wallet.pubkey()}")
    print(f"💰 Balance: {balance_sol:.6f} SOL")
    print()
    
    # Calculate recommendations
    reserve = 0.02
    stakeable = balance_sol - reserve
    
    if stakeable > 0:
        print("📈 Empfohlener Auto-Stake:")
        print(f"   Stakeable Amount: {stakeable:.6f} SOL (90%)")
        print(f"   Gas Reserve: {reserve:.6f} SOL")
        print()
        
        print("💰 Jährliches Potenzial:")
        for token, info in sorted(TOKENS.items(), key=lambda x: x[1]['apy'], reverse=True):
            yearly_gain = stakeable * (info['apy'] / 100)
            print(f"   {token:10s}: +{yearly_gain:.6f} SOL ({info['apy']}% APY)")
    else:
        print("⚠️  Balance zu niedrig für Staking")
        print(f"   Minimum: {reserve + 0.01:.2f} SOL benötigt")
    
    print()
    print("🚀 Nächste Schritte:")
    print("   1. Jupiter Web: https://jup.ag/swap/SOL-jitoSOL")
    print("   2. Oder: python quick_stake_demo.py")
    print("   3. Setze: ALLOW_REAL_TRANSACTIONS=true in .env.production")

except Exception as e:
    print(f"❌ Fehler: {e}")
    print()
    print("⚠️  Stelle sicher dass .env.production konfiguriert ist")

print()
print("=" * 70)
