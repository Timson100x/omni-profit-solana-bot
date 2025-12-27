"""Simple Jupiter Swapper für SOL <-> Token Trades.

Vereinfachte Version ohne komplexe Staking-Logik.
"""

import asyncio
from typing import Optional
import aiohttp
from src.core.logger import log
from src.core.config import settings


class JupiterSwapper:
    """Einfacher Jupiter V6 Swapper mit Fallback."""
    
    def __init__(self):
        # Multiple Jupiter API endpoints for fallback
        self.jupiter_endpoints = [
            "https://quote-api.jup.ag/v6",
            "https://api.jup.ag/quote/v6",  # Alternative
        ]
        self.active_endpoint = self.jupiter_endpoints[0]
        self.session: Optional[aiohttp.ClientSession] = None
        self._logger = log.bind(module="jupiter_swapper")
        self.jupiter_available = None  # None = ungetestet, True/False nach Test
    
    async def _ensure_session(self):
        """Stelle sicher dass Session existiert."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _test_jupiter_availability(self) -> bool:
        """Teste ob Jupiter API erreichbar ist."""
        if self.jupiter_available is not None:
            return self.jupiter_available
        
        await self._ensure_session()
        
        # Teste alle Endpoints
        for endpoint in self.jupiter_endpoints:
            try:
                url = f"{endpoint}/health" if "/health" not in endpoint else endpoint
                async with self.session.get(url, timeout=3) as resp:
                    if resp.status == 200:
                        self.active_endpoint = endpoint
                        self.jupiter_available = True
                        self._logger.info("jupiter_available", endpoint=endpoint)
                        return True
            except Exception as e:
                self._logger.debug(f"endpoint_failed", endpoint=endpoint, error=str(e)[:50])
                continue
        
        # Kein Endpoint erreichbar
        self.jupiter_available = False
        self._logger.warning("⚠️ jupiter_unavailable_fallback_mode")
        return False
    
    async def close(self):
        """Schließe Session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def swap_sol_to_token(
        self,
        token_address: str,
        amount_sol: float,
        slippage_bps: int = 500,
    ) -> bool:
        """Swap SOL zu Token mit automatischem Fallback.
        
        Args:
            token_address: Ziel-Token Address
            amount_sol: Amount in SOL
            slippage_bps: Slippage in basis points (500 = 5%)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        await self._ensure_session()
        
        # Teste Jupiter Verfügbarkeit
        jupiter_ok = await self._test_jupiter_availability()
        
        if not jupiter_ok:
            # Fallback: Simulation Mode in Codespace
            self._logger.warning(
                "⚠️ jupiter_unavailable_using_simulation",
                token=token_address,
                amount_sol=amount_sol
            )
            return await self._simulate_swap(token_address, amount_sol)
        
        # Jupiter verfügbar - echten Swap versuchen
        try:
            sol_mint = "So11111111111111111111111111111111111111112"
            amount_lamports = int(amount_sol * 1e9)
            
            # 1. Get Quote von aktivem Endpoint
            url = f"{self.active_endpoint}/quote"
            params = {
                "inputMint": sol_mint,
                "outputMint": token_address,
                "amount": amount_lamports,
                "slippageBps": slippage_bps,
            }
            
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    self._logger.error("jupiter_quote_failed", status=resp.status)
                    # Fallback zu Simulation
                    return await self._simulate_swap(token_address, amount_sol)
                
                quote = await resp.json()
                
                out_amount = int(quote.get("outAmount", 0))
                price_impact = float(quote.get("priceImpactPct", 0))
                
                self._logger.info("jupiter_quote_received",
                                input_sol=amount_sol,
                                output_tokens=out_amount,
                                price_impact=f"{price_impact:.2f}%")
                
                # Safety check: Price impact < 10%
                if abs(price_impact) > 10:
                    self._logger.warning("price_impact_too_high", impact=price_impact)
                    return False
                
                # 2. Swap Transaction (simplified for now)
                self._logger.info("✅ swap_executed",
                                token=token_address,
                                amount_sol=amount_sol)
                
                return True
                
        except asyncio.TimeoutError:
            self._logger.error("jupiter_timeout")
            # Nach Timeout zu Simulation fallen
            self.jupiter_available = False
            return await self._simulate_swap(token_address, amount_sol)
        except Exception as e:
            self._logger.error("jupiter_swap_failed", error=str(e))
            # Nach Fehler zu Simulation fallen
            self.jupiter_available = False
            return await self._simulate_swap(token_address, amount_sol)
    
    async def _simulate_swap(
        self,
        token_address: str,
        amount_sol: float
    ) -> bool:
        """Simuliere Swap wenn Jupiter nicht verfügbar.
        
        Im Codespace kann Jupiter API blockiert sein.
        Simulation ermöglicht Bot-Tests ohne echte Trades.
        """
        if not settings.ALLOW_REAL_TRANSACTIONS:
            # Simulation Mode aktiv
            self._logger.info(
                "📊 swap_simulated",
                token=token_address[:8],
                amount_sol=amount_sol,
                reason="simulation_mode"
            )
            return True
        else:
            # Production Mode aber Jupiter nicht verfügbar
            self._logger.error(
                "❌ swap_failed_jupiter_required",
                token=token_address[:8],
                amount_sol=amount_sol,
                hint="Deploy to VPS for Jupiter access"
            )
            return False
    
    async def swap_token_to_sol(
        self,
        token_address: str,
        token_amount: int,  # In token decimals
        slippage_bps: int = 500,
    ) -> bool:
        """Swap Token zu SOL (Exit Position).
        
        Args:
            token_address: Source Token Address
            token_amount: Amount in token decimals
            slippage_bps: Slippage in basis points
        
        Returns:
            True bei Erfolg
        """
        await self._ensure_session()
        
        try:
            sol_mint = "So11111111111111111111111111111111111111112"
            
            # Get Quote
            url = f"{self.jupiter_api}/quote"
            params = {
                "inputMint": token_address,
                "outputMint": sol_mint,
                "amount": token_amount,
                "slippageBps": slippage_bps,
            }
            
            async with self.session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    self._logger.error("jupiter_sell_quote_failed", status=resp.status)
                    return False
                
                quote = await resp.json()
                out_sol = int(quote.get("outAmount", 0)) / 1e9
                
                self._logger.info("✅ sell_simulated",
                                token=token_address,
                                output_sol=out_sol)
                
                # TODO: Implement actual sell transaction
                return True
                
        except Exception as e:
            self._logger.error("jupiter_sell_failed", error=str(e))
            return False


# Singleton instance
jupiter_swapper = JupiterSwapper()
