#!/usr/bin/env python3
"""Live Test: Finde echte Memecoins auf Solana."""

import asyncio
import sys
import aiohttp
from datetime import datetime

sys.path.insert(0, '/workspaces/omni-profit-solana-bot')

from src.signals.validator import SignalValidator

async def fetch_trending_memecoins():
    """Hole trending Solana Memecoins von DexScreener."""
    
    print("🔍 Suche nach trending Solana Memecoins...")
    print()
    
    async with aiohttp.ClientSession() as session:
        try:
            url = "https://api.dexscreener.com/latest/dex/search?q=Solana"
            
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    print(f"❌ DexScreener API Error: {resp.status}")
                    return []
                
                data = await resp.json()
                pairs = data.get('pairs', [])
                
                solana_pairs = [p for p in pairs if p.get('chainId') == 'solana']
                solana_pairs.sort(key=lambda x: float(x.get('volume', {}).get('h24', 0)), reverse=True)
                
                print(f"✅ Gefunden: {len(solana_pairs)} Solana Tokens")
                print()
                
                return solana_pairs[:10]
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def test_memecoin_detection():
    """Teste ob Bot Memecoins findet."""
    
    print("=" * 70)
    print("🎯 LIVE TEST: Memecoin Detection")
    print("=" * 70)
    print()
    
    tokens = await fetch_trending_memecoins()
    
    if not tokens:
        print("❌ Keine Tokens gefunden")
        return
    
    print("📊 Top Trending Tokens:")
    print()
    
    for i, token in enumerate(tokens[:5], 1):
        base = token.get('baseToken', {})
        price_change = token.get('priceChange', {}).get('h24', 0)
        volume = token.get('volume', {}).get('h24', 0)
        liquidity = token.get('liquidity', {}).get('usd', 0)
        
        print(f"{i}. {base.get('name', 'Unknown')} ({base.get('symbol', '???')})")
        print(f"   Address: {base.get('address', 'N/A')}")
        print(f"   Price: ${float(token.get('priceUsd', 0)):.8f}")
        print(f"   24h Change: {price_change:+.2f}%")
        print(f"   Volume: ${volume:,.0f}")
        print(f"   Liquidity: ${liquidity:,.0f}")
        print()
    
    print("=" * 70)
    print("🔍 Validierung mit 8-Check System")
    print("=" * 70)
    print()
    
    async with SignalValidator() as validator:
        valid_count = 0
        rejected_count = 0
        
        for i, token in enumerate(tokens[:3], 1):
            base = token.get('baseToken', {})
            token_addr = base.get('address')
            token_name = base.get('name', 'Unknown')
            
            print(f"Testing {i}/3: {token_name}")
            print(f"Address: {token_addr}")
            print()
            
            if not token_addr:
                continue
            
            result = await validator.validate_signal(token_addr, source_channel="dexscreener")
            
            if result.is_valid:
                valid_count += 1
                print(f"   ✅ VALID - Score: {result.score}/100")
                print(f"   📊 Checks:")
                for check, passed in result.checks.items():
                    print(f"      {'✅' if passed else '❌'} {check}")
                print()
                if result.warnings:
                    print(f"   ⚠️  Warnings:")
                    for w in result.warnings[:2]:
                        print(f"      • {w}")
                print()
                print(f"   🚀 WOULD TRADE")
            else:
                rejected_count += 1
                print(f"   ❌ REJECTED - Score: {result.score}/100")
                print(f"   ⚠️  Warnings:")
                for w in result.warnings[:3]:
                    print(f"      • {w}")
                print()
                print(f"   🛑 WOULD SKIP")
            
            print("-" * 70)
            print()
    
    print("=" * 70)
    print("📈 Test Summary")
    print("=" * 70)
    print()
    print(f"Valid: {valid_count} ✅")
    print(f"Rejected: {rejected_count} ❌")
    print()
    
    if valid_count > 0:
        print("🎉 SUCCESS: Bot kann Memecoins finden!")
    else:
        print("⚠️  Validation sehr streng - eventuell Score senken")

if __name__ == "__main__":
    asyncio.run(test_memecoin_detection())
