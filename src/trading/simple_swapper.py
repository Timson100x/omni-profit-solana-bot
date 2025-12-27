"""Simple Jupiter Swapper für SOL <-> Token Trades.

Vereinfachte Version ohne komplexe Staking-Logik.
"""

import asyncio
import base64
from typing import Optional
import aiohttp
from src.core.logger import log
from src.core.config import settings
from src.blockchain.wallet import wallet_manager
from src.blockchain.client import solana_client
from solders.transaction import VersionedTransaction


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
                
                # 2. In Simulation nur loggen
                if not settings.ALLOW_REAL_TRANSACTIONS:
                    self._logger.info("📊 swap_simulated",
                                    token=token_address,
                                    amount_sol=amount_sol,
                                    reason="simulation_mode")
                    return True

                # 3. Real Swap: Build swap tx via Jupiter + sign + send
                wallet_manager.load_wallet()
                keypair = wallet_manager.get_keypair()
                user_pubkey = str(keypair.pubkey())

                swap_url = f"{self.active_endpoint}/swap"
                payload = {
                    "quoteResponse": quote,
                    "userPublicKey": user_pubkey,
                    "wrapAndUnwrapSol": True,
                    # keep conservative defaults
                    "asLegacyTransaction": False,
                }

                async with self.session.post(swap_url, json=payload) as resp:
                    if resp.status != 200:
                        error_msg = await resp.text()
                        self._logger.error("jupiter_swap_failed", status=resp.status, error=error_msg[:200])
                        return False

                    swap_data = await resp.json()
                    swap_tx_b64 = swap_data.get("swapTransaction")

                if not swap_tx_b64:
                    self._logger.error("jupiter_swap_missing_transaction")
                    return False

                raw_tx = base64.b64decode(swap_tx_b64)
                vtx = VersionedTransaction.from_bytes(raw_tx)

                sig = keypair.sign_message(bytes(vtx.message))
                sigs = list(vtx.signatures)
                if not sigs:
                    # Jupiter should provide signature slots, but be defensive
                    sigs = [sig]
                else:
                    sigs[0] = sig

                signed = VersionedTransaction.populate(vtx.message, sigs)

                await solana_client.connect()
                send_resp = await solana_client.client.send_raw_transaction(
                    bytes(signed),
                    opts={
                        "skip_preflight": True,
                        "preflight_commitment": "confirmed",
                    },
                )

                self._logger.info(
                    "✅ swap_sent",
                    token=token_address,
                    amount_sol=amount_sol,
                    signature=str(send_resp.value)[:16] if getattr(send_resp, "value", None) else None,
                )
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
        """Execute/Simuliere Swap mit mehreren Fallback-Methoden.
        
        Priority:
        1. On-Chain Swapper (funktioniert in Codespace!)
        2. Raydium DEX API
        3. Simulation Mode
        """
        # PRIORITY #1: On-Chain Swapper (nutzt nur Helius RPC)
        try:
            from src.trading.onchain_swapper import onchain_swapper
            
            self._logger.info("🔗 trying_onchain_swapper",
                            token=token_address[:8],
                            amount_sol=amount_sol)
            
            success = await onchain_swapper.swap_sol_to_token(
                token_address=token_address,
                amount_sol=amount_sol,
                slippage_bps=500
            )
            
            if success:
                self._logger.info("✅ onchain_swap_success",
                                token=token_address[:8])
                return True
            else:
                self._logger.warning("onchain_swap_failed")
                
        except Exception as e:
            self._logger.error("onchain_swapper_error", error=str(e)[:50])
        
        # PRIORITY #2: Raydium Fallback
        if settings.ALLOW_REAL_TRANSACTIONS:
            try:
                from src.trading.raydium_swapper import raydium_swapper
                
                self._logger.info("🔄 trying_raydium_fallback",
                                token=token_address[:8],
                                amount_sol=amount_sol)
                
                success = await raydium_swapper.swap_sol_to_token(
                    token_address=token_address,
                    amount_sol=amount_sol,
                    slippage_bps=500
                )
                
                if success:
                    self._logger.info("✅ raydium_swap_success",
                                    token=token_address[:8])
                    return True
                else:
                    self._logger.warning("raydium_also_failed")
                    
            except Exception as e:
                self._logger.error("raydium_error", error=str(e)[:50])
        
        # PRIORITY #3: Simulation Mode
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
            # Production Mode aber alle Swaps fehlgeschlagen
            self._logger.error(
                "❌ swap_failed_all_methods",
                token=token_address[:8],
                amount_sol=amount_sol,
                hint="Check Helius RPC or deploy to VPS"
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
            url = f"{self.active_endpoint}/quote"
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

                if not settings.ALLOW_REAL_TRANSACTIONS:
                    self._logger.info(
                        "📊 sell_simulated",
                        token=token_address,
                        output_sol=out_sol,
                        reason="simulation_mode",
                    )
                    return True

                wallet_manager.load_wallet()
                keypair = wallet_manager.get_keypair()
                user_pubkey = str(keypair.pubkey())

                swap_url = f"{self.active_endpoint}/swap"
                payload = {
                    "quoteResponse": quote,
                    "userPublicKey": user_pubkey,
                    "wrapAndUnwrapSol": True,
                    "asLegacyTransaction": False,
                }

                async with self.session.post(swap_url, json=payload) as resp:
                    if resp.status != 200:
                        error_msg = await resp.text()
                        self._logger.error("jupiter_sell_swap_failed", status=resp.status, error=error_msg[:200])
                        return False

                    swap_data = await resp.json()
                    swap_tx_b64 = swap_data.get("swapTransaction")

                if not swap_tx_b64:
                    self._logger.error("jupiter_sell_missing_transaction")
                    return False

                raw_tx = base64.b64decode(swap_tx_b64)
                vtx = VersionedTransaction.from_bytes(raw_tx)

                sig = keypair.sign_message(bytes(vtx.message))
                sigs = list(vtx.signatures)
                if not sigs:
                    sigs = [sig]
                else:
                    sigs[0] = sig

                signed = VersionedTransaction.populate(vtx.message, sigs)

                await solana_client.connect()
                send_resp = await solana_client.client.send_raw_transaction(
                    bytes(signed),
                    opts={
                        "skip_preflight": True,
                        "preflight_commitment": "confirmed",
                    },
                )

                self._logger.info(
                    "✅ sell_sent",
                    token=token_address,
                    output_sol=out_sol,
                    signature=str(send_resp.value)[:16] if getattr(send_resp, "value", None) else None,
                )
                return True
                
        except Exception as e:
            self._logger.error("jupiter_sell_failed", error=str(e))
            return False


# Singleton instance
jupiter_swapper = JupiterSwapper()
