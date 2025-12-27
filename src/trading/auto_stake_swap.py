"""Auto-Stake Swap Service mit Jupiter Integration.

Konvertiert automatisch SOL zu Liquid Staking Tokens (mSOL, rSOL, jitoSOL)
für passives Einkommen während des Tradings.
"""

import os
import asyncio
from typing import Optional, Literal
from dataclasses import dataclass
from decimal import Decimal

import aiohttp
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

from src.core.logger import log
from src.core.config import settings
from src.blockchain.wallet import get_wallet

# Token Adressen
TOKENS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "mSOL": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",  # Marinade - 7.0% APY
    "rSOL": "rSoLbUZpGbhKT8azFTvWLSNYKQvqoQEGKqC7pzDnBsP",  # Raydium - 6.5% APY
    "jitoSOL": "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",  # Jito - 7.5% APY
    "bSOL": "bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1",  # BlazeStake - 6.8% APY
}

StakingToken = Literal["mSOL", "rSOL", "jitoSOL", "bSOL"]


@dataclass
class SwapQuote:
    """Jupiter Swap Quote."""
    input_mint: str
    output_mint: str
    in_amount: int
    out_amount: int
    price_impact_pct: float
    route_plan: list


@dataclass
class SwapResult:
    """Swap Ausführungs-Ergebnis."""
    success: bool
    signature: Optional[str] = None
    input_amount: Optional[float] = None
    output_amount: Optional[float] = None
    error: Optional[str] = None


class AutoStakeSwap:
    """Automatischer SOL → Staking Token Swap via Jupiter."""
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        wallet_key: Optional[str] = None,
        allow_real_tx: bool = False,
    ):
        self.rpc_url = rpc_url or settings.SOLANA_RPC_URL
        self.wallet_key = wallet_key or settings.WALLET_PRIVATE_KEY
        self.allow_real_tx = allow_real_tx or settings.ALLOW_REAL_TRANSACTIONS
        self.client: Optional[AsyncClient] = None
        self.wallet: Optional[Keypair] = None
        
        # Jupiter API V6
        self.jupiter_api = "https://quote-api.jup.ag/v6"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    async def initialize(self):
        """Initialisiere Clients."""
        self.client = AsyncClient(self.rpc_url)
        self.wallet = get_wallet(self.wallet_key)
        self.session = aiohttp.ClientSession()
        log.info("auto_stake_swap_initialized", wallet=str(self.wallet.pubkey()))
    
    async def close(self):
        """Schließe Connections."""
        if self.client:
            await self.client.close()
        if self.session:
            await self.session.close()
    
    async def get_sol_balance(self) -> float:
        """Hole SOL Balance."""
        response = await self.client.get_balance(self.wallet.pubkey())
        if response.value is None:
            return 0.0
        return float(response.value) / 1e9
    
    async def get_quote(
        self,
        from_token: str,
        to_token: StakingToken,
        amount_sol: float,
        slippage_bps: int = 50,  # 0.5% default
    ) -> Optional[SwapQuote]:
        """Hole Jupiter Swap Quote.
        
        Args:
            from_token: Input token (z.B. "SOL")
            to_token: Output staking token (z.B. "mSOL")
            amount_sol: Amount in SOL
            slippage_bps: Slippage in basis points (50 = 0.5%)
        
        Returns:
            SwapQuote oder None bei Fehler
        """
        input_mint = TOKENS[from_token]
        output_mint = TOKENS[to_token]
        amount_lamports = int(amount_sol * 1e9)
        
        url = f"{self.jupiter_api}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_lamports,
            "slippageBps": slippage_bps,
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "false",
        }
        
        try:
            async with self.session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    log.error("jupiter_quote_failed", status=resp.status)
                    return None
                
                data = await resp.json()
                
                return SwapQuote(
                    input_mint=input_mint,
                    output_mint=output_mint,
                    in_amount=int(data["inAmount"]),
                    out_amount=int(data["outAmount"]),
                    price_impact_pct=float(data.get("priceImpactPct", 0)),
                    route_plan=data.get("routePlan", []),
                )
        
        except Exception as e:
            log.error("jupiter_quote_error", error=str(e))
            return None
    
    async def execute_swap(
        self,
        quote: SwapQuote,
        simulate_only: bool = True,
    ) -> SwapResult:
        """Führe Swap aus.
        
        Args:
            quote: Jupiter Quote
            simulate_only: Nur simulieren, nicht ausführen
        
        Returns:
            SwapResult mit Erfolg/Fehler
        """
        if not self.allow_real_tx or simulate_only:
            log.info(
                "auto_stake_swap_simulated",
                in_amount_sol=quote.in_amount / 1e9,
                out_amount=quote.out_amount / 1e9,
                price_impact=quote.price_impact_pct,
            )
            return SwapResult(
                success=True,
                input_amount=quote.in_amount / 1e9,
                output_amount=quote.out_amount / 1e9,
            )
        
        # Realer Swap via Jupiter API
        try:
            # 1. Get swap transaction
            url = f"{self.jupiter_api}/swap"
            payload = {
                "quoteResponse": {
                    "inputMint": quote.input_mint,
                    "outputMint": quote.output_mint,
                    "inAmount": str(quote.in_amount),
                    "outAmount": str(quote.out_amount),
                    "routePlan": quote.route_plan,
                },
                "userPublicKey": str(self.wallet.pubkey()),
                "wrapAndUnwrapSol": True,
            }
            
            async with self.session.post(url, json=payload, timeout=10) as resp:
                if resp.status != 200:
                    error_msg = await resp.text()
                    log.error("jupiter_swap_failed", status=resp.status, error=error_msg)
                    return SwapResult(success=False, error=error_msg)
                
                swap_data = await resp.json()
                swap_transaction = swap_data["swapTransaction"]
            
            # 2. Sign and send transaction
            # TODO: Implement transaction signing and sending
            log.warning("real_swap_not_implemented", message="Transaction signing coming soon")
            
            return SwapResult(
                success=False,
                error="Real transaction execution not yet implemented",
            )
        
        except Exception as e:
            log.error("swap_execution_error", error=str(e))
            return SwapResult(success=False, error=str(e))
    
    async def auto_stake(
        self,
        target_token: StakingToken = "mSOL",
        percentage: float = 90.0,
        min_reserve_sol: float = 0.02,
        simulate_only: bool = True,
    ) -> SwapResult:
        """Automatisch SOL zu Staking Token konvertieren.
        
        Args:
            target_token: Ziel-Token (mSOL, rSOL, jitoSOL, bSOL)
            percentage: Prozent der Balance zu konvertieren (default 90%)
            min_reserve_sol: Minimum SOL Reserve für Gas (default 0.02)
            simulate_only: Nur simulieren
        
        Returns:
            SwapResult
        """
        # 1. Check balance
        balance = await self.get_sol_balance()
        log.info("auto_stake_check_balance", balance=balance)
        
        if balance < min_reserve_sol:
            return SwapResult(
                success=False,
                error=f"Balance too low: {balance} SOL < {min_reserve_sol} minimum",
            )
        
        # 2. Calculate swap amount
        available = balance - min_reserve_sol
        swap_amount = available * (percentage / 100.0)
        
        if swap_amount <= 0:
            return SwapResult(
                success=False,
                error=f"No SOL available to swap after reserve: {available} SOL",
            )
        
        log.info(
            "auto_stake_params",
            balance=balance,
            swap_amount=swap_amount,
            reserve=min_reserve_sol,
            target=target_token,
        )
        
        # 3. Get quote
        quote = await self.get_quote("SOL", target_token, swap_amount)
        if not quote:
            return SwapResult(success=False, error="Failed to get quote from Jupiter")
        
        # 4. Check price impact
        if quote.price_impact_pct > 2.0:
            log.warning(
                "high_price_impact",
                impact=quote.price_impact_pct,
                message="Price impact > 2%, consider smaller amount",
            )
        
        # 5. Execute swap
        result = await self.execute_swap(quote, simulate_only=simulate_only)
        
        if result.success:
            log.info(
                "auto_stake_success",
                input=result.input_amount,
                output=result.output_amount,
                token=target_token,
                simulated=simulate_only,
            )
        
        return result


async def main():
    """CLI Demo."""
    print("=" * 70)
    print("🚀 Auto-Stake Swap - Jupiter Integration")
    print("=" * 70)
    print()
    
    # Load config
    from dotenv import load_dotenv
    load_dotenv(".env.production")
    
    async with AutoStakeSwap() as swapper:
        # Show balance
        balance = await swapper.get_sol_balance()
        print(f"💰 Aktuelle Balance: {balance:.6f} SOL")
        print()
        
        # Show options
        print("📊 Verfügbare Staking Tokens:")
        print("   1. mSOL (Marinade)   - 7.0% APY")
        print("   2. rSOL (Raydium)    - 6.5% APY")
        print("   3. jitoSOL (Jito)    - 7.5% APY")
        print("   4. bSOL (BlazeStake) - 6.8% APY")
        print()
        
        # Demo swap
        target = "mSOL"
        print(f"🔄 Demo: SOL → {target}")
        print()
        
        result = await swapper.auto_stake(
            target_token=target,
            percentage=90.0,
            simulate_only=True,
        )
        
        if result.success:
            print(f"✅ Swap erfolgreich (Simulation)")
            print(f"   Input:  {result.input_amount:.6f} SOL")
            print(f"   Output: {result.output_amount:.6f} {target}")
            print(f"   Rate:   {result.output_amount/result.input_amount:.4f}")
        else:
            print(f"❌ Swap fehlgeschlagen: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
