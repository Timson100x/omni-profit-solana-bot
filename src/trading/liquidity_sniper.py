"""Liquidity Sniper - Monitor neue Pools für First Buyer Advantage.

WebSocket monitoring für Raydium/Orca Pool Creations.
"""

import asyncio
import json
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass

import websockets
from solders.pubkey import Pubkey

from src.core.logger import log
from src.core.config import settings
from src.signals.validator import signal_validator
from src.trading.manager import trade_manager


@dataclass
class NewPool:
    """Neuer Liquiditätspool."""
    pool_address: str
    token_address: str
    dex: str  # raydium, orca
    initial_liquidity_sol: float
    detected_at: datetime


class LiquiditySniper:
    """Monitor neue Pools und snipe first buy.
    
    Strategy:
    1. WebSocket zu Raydium/Orca Program
    2. Neue Pool Creation detected
    3. Validate Pool (liquidity, safety)
    4. Execute buy mit Max Priority Fee
    5. Target: 3-10x in 1-30 minutes
    """
    
    # Program IDs
    RAYDIUM_AMM_V4 = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
    ORCA_WHIRLPOOL = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
    
    def __init__(
        self,
        ws_url: str = "wss://api.mainnet-beta.solana.com",
        min_liquidity_sol: float = 5.0,
        max_buy_sol: float = 0.1,
    ):
        """
        Args:
            ws_url: Solana WebSocket URL
            min_liquidity_sol: Minimum Pool Liquidity
            max_buy_sol: Maximum buy amount per snipe
        """
        self.ws_url = ws_url
        self.min_liquidity_sol = min_liquidity_sol
        self.max_buy_sol = max_buy_sol
        
        self.sniped_pools: set = set()  # Avoid duplicate snipes
        self.stats = {
            'pools_detected': 0,
            'pools_sniped': 0,
            'pools_rejected': 0,
        }
    
    async def start_monitoring(self, dex: str = "raydium"):
        """Start monitoring für neue Pools.
        
        Args:
            dex: "raydium" oder "orca"
        """
        program_id = self.RAYDIUM_AMM_V4 if dex == "raydium" else self.ORCA_WHIRLPOOL
        
        log.info("sniper_starting", dex=dex, program=program_id)
        print(f"🎯 Liquidity Sniper gestartet - {dex.upper()}")
        print(f"   Min Liquidity: {self.min_liquidity_sol} SOL")
        print(f"   Max Buy: {self.max_buy_sol} SOL")
        print()
        
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    # Subscribe to program logs
                    subscribe = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "logsSubscribe",
                        "params": [
                            {"mentions": [program_id]},
                            {"commitment": "confirmed"}
                        ]
                    }
                    
                    await ws.send(json.dumps(subscribe))
                    log.info("sniper_subscribed", dex=dex)
                    
                    # Process incoming logs
                    async for message in ws:
                        await self._process_log(message, dex)
            
            except websockets.exceptions.ConnectionClosed:
                log.warning("sniper_disconnected", dex=dex)
                await asyncio.sleep(5)
            
            except Exception as e:
                log.error("sniper_error", dex=dex, error=str(e))
                await asyncio.sleep(10)
    
    async def _process_log(self, message: str, dex: str):
        """Process WebSocket log message.
        
        Args:
            message: WebSocket message
            dex: DEX name
        """
        try:
            data = json.loads(message)
            
            if 'result' not in data:
                return
            
            result = data['result']
            
            if 'value' not in result:
                return
            
            value = result['value']
            logs = value.get('logs', [])
            
            # Check for pool initialization
            is_pool_init = any(
                'initialize' in log.lower() or 'create' in log.lower()
                for log in logs
            )
            
            if not is_pool_init:
                return
            
            self.stats['pools_detected'] += 1
            
            # Extract pool info from signature
            signature = value.get('signature', '')
            
            log.info(
                "pool_detected",
                dex=dex,
                signature=signature[:16],
            )
            
            print(f"🚨 NEW POOL DETECTED - {dex.upper()}")
            print(f"   Signature: {signature[:32]}...")
            
            # Analyze pool
            await self._analyze_and_snipe(signature, dex)
        
        except Exception as e:
            log.debug("log_process_error", error=str(e))
    
    async def _analyze_and_snipe(self, signature: str, dex: str):
        """Analyze pool and execute snipe if valid.
        
        Args:
            signature: Transaction signature
            dex: DEX name
        """
        # Avoid duplicate snipes
        if signature in self.sniped_pools:
            return
        
        self.sniped_pools.add(signature)
        
        try:
            # TODO: Extract pool and token address from transaction
            # For now, mock data
            pool_address = f"pool_{signature[:8]}"
            token_address = f"token_{signature[8:16]}"
            
            print(f"   Analyzing pool...")
            
            # Validate token
            result = await signal_validator.validate_signal(
                token_address,
                source_channel=f"sniper_{dex}",
            )
            
            print(f"   Validation Score: {result.score}/100")
            
            # Minimum score for sniping (more lenient than normal)
            if result.score < 50:
                self.stats['pools_rejected'] += 1
                print(f"   ❌ REJECTED - Score too low")
                print()
                return
            
            # Check critical flags
            critical_checks = [
                'safe_contract',
                'liquidity',
            ]
            
            if not all(result.checks.get(k, False) for k in critical_checks):
                self.stats['pools_rejected'] += 1
                print(f"   ❌ REJECTED - Failed critical checks")
                print()
                return
            
            # SNIPE!
            print(f"   ✅ VALID - Executing snipe...")
            
            if settings.ALLOW_REAL_TRANSACTIONS:
                # Execute with max priority
                token_data = {
                    'address': token_address,
                    'name': f'SNIPE_{dex}',
                    'price_usd': 0.0001,  # Estimated
                }
                
                analysis = {
                    'confidence': 0.8,  # High for sniping
                    'reason': f'New pool snipe - {dex}',
                    'target_multiplier': 5.0,  # Aggressive target
                }
                
                success = await trade_manager.execute_trade(token_data, analysis)
                
                if success:
                    self.stats['pools_sniped'] += 1
                    print(f"   🚀 SNIPED! Target: 5x")
                else:
                    print(f"   ❌ Snipe failed")
            else:
                self.stats['pools_sniped'] += 1
                print(f"   🎯 SNIPE (Simulation Mode)")
            
            print()
        
        except Exception as e:
            log.error("snipe_error", signature=signature, error=str(e))
            print(f"   ❌ Error: {e}")
            print()
    
    def get_stats(self) -> Dict:
        """Get sniper statistics."""
        return {
            **self.stats,
            'success_rate': (
                self.stats['pools_sniped'] / self.stats['pools_detected']
                if self.stats['pools_detected'] > 0
                else 0
            ),
        }


async def run_sniper(dex: str = "raydium"):
    """Start liquidity sniper.
    
    Args:
        dex: "raydium" or "orca"
    """
    sniper = LiquiditySniper(
        min_liquidity_sol=5.0,
        max_buy_sol=0.1,
    )
    
    try:
        await sniper.start_monitoring(dex=dex)
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("🛑 Sniper gestoppt")
        print("=" * 70)
        print()
        
        stats = sniper.get_stats()
        print("📊 Statistics:")
        print(f"   Pools Detected: {stats['pools_detected']}")
        print(f"   Pools Sniped:   {stats['pools_sniped']}")
        print(f"   Pools Rejected: {stats['pools_rejected']}")
        print(f"   Success Rate:   {stats['success_rate']*100:.1f}%")


async def main():
    """CLI Entry Point."""
    print("=" * 70)
    print("🎯 Liquidity Sniper - First Buyer Advantage")
    print("=" * 70)
    print()
    
    print("⚠️  WARNING: High Risk Strategy!")
    print("   - New tokens can be scams")
    print("   - Many pools rug pull")
    print("   - Only invest what you can lose")
    print()
    print("💡 Strategy:")
    print("   1. Monitor new Raydium pools")
    print("   2. Validate token safety")
    print("   3. Buy with max priority fee")
    print("   4. Target: 3-10x in minutes")
    print("   5. Auto-exit at target or -50%")
    print()
    
    choice = input("Start sniper? (yes/no): ").strip().lower()
    
    if choice != "yes":
        print("❌ Aborted")
        return
    
    print()
    print("🚀 Starting Raydium sniper...")
    print()
    
    await run_sniper(dex="raydium")


if __name__ == "__main__":
    asyncio.run(main())
