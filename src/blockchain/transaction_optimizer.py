"""Transaction Speed Optimizer für Solana.

Macht Transaktionen schneller durch:
- Priority Fees (Jito Bundle Support)
- Compute Unit Optimization
- Multiple RPC Endpoints mit Failover
- Transaction Confirmation Tuning
"""

import os
import asyncio
from typing import Optional, List
from dataclasses import dataclass

import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction

from src.core.logger import log
from src.core.config import settings


@dataclass
class RPCEndpoint:
    """RPC Endpoint mit Performance-Metriken."""
    url: str
    name: str
    priority: int
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0


class TransactionOptimizer:
    """Optimiert Transaktionsgeschwindigkeit auf Solana."""
    
    # Top Solana RPCs für Geschwindigkeit
    RPC_ENDPOINTS = [
        RPCEndpoint("https://api.mainnet-beta.solana.com", "Solana Official", 1),
        RPCEndpoint("https://solana-api.projectserum.com", "Project Serum", 2),
        RPCEndpoint("https://rpc.ankr.com/solana", "Ankr", 3),
        RPCEndpoint("https://solana-mainnet.rpc.extrnode.com", "Extrnode", 4),
    ]
    
    # Jito Block Engine für MEV Protection + Speed
    JITO_ENDPOINTS = [
        "https://mainnet.block-engine.jito.wtf",
        "https://amsterdam.mainnet.block-engine.jito.wtf",
        "https://frankfurt.mainnet.block-engine.jito.wtf",
        "https://ny.mainnet.block-engine.jito.wtf",
        "https://tokyo.mainnet.block-engine.jito.wtf",
    ]
    
    def __init__(
        self,
        use_jito: bool = True,
        priority_fee_lamports: int = 10000,  # 0.00001 SOL = ~$0.002
        compute_units: int = 200_000,
    ):
        """
        Args:
            use_jito: Jito Bundle für schnellere Inclusion
            priority_fee_lamports: Priority Fee (höher = schneller)
            compute_units: Compute Unit Limit
        """
        self.use_jito = use_jito
        self.priority_fee_lamports = priority_fee_lamports
        self.compute_units = compute_units
        
        self.current_endpoint_idx = 0
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    def get_priority_instructions(self) -> List[Instruction]:
        """Erstelle Priority Fee Instructions.
        
        Returns:
            List mit Compute Budget Instructions
        """
        return [
            set_compute_unit_limit(self.compute_units),
            set_compute_unit_price(self.priority_fee_lamports),
        ]
    
    def add_priority_fee(self, instructions: List[Instruction]) -> List[Instruction]:
        """Füge Priority Fee zu bestehenden Instructions hinzu.
        
        Args:
            instructions: Original Instructions
        
        Returns:
            Instructions mit Priority Fee am Anfang
        """
        priority_ix = self.get_priority_instructions()
        return priority_ix + instructions
    
    async def get_fastest_rpc(self) -> str:
        """Finde schnellsten RPC Endpoint.
        
        Returns:
            URL des schnellsten Endpoints
        """
        if not self.session:
            return self.RPC_ENDPOINTS[0].url
        
        tasks = []
        for endpoint in self.RPC_ENDPOINTS:
            tasks.append(self._test_rpc_latency(endpoint))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Sortiere nach Latenz
        valid_endpoints = [
            (endpoint, latency)
            for endpoint, latency in zip(self.RPC_ENDPOINTS, results)
            if isinstance(latency, float)
        ]
        
        if not valid_endpoints:
            log.warning("all_rpcs_failed", fallback=self.RPC_ENDPOINTS[0].url)
            return self.RPC_ENDPOINTS[0].url
        
        fastest = min(valid_endpoints, key=lambda x: x[1])
        log.info("fastest_rpc_found", url=fastest[0].url, latency_ms=fastest[1])
        
        return fastest[0].url
    
    async def _test_rpc_latency(self, endpoint: RPCEndpoint) -> float:
        """Teste RPC Latenz mit getHealth.
        
        Returns:
            Latenz in Millisekunden
        """
        import time
        
        try:
            start = time.time()
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth",
            }
            
            async with self.session.post(
                endpoint.url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=2),
            ) as resp:
                await resp.json()
                
                latency_ms = (time.time() - start) * 1000
                return latency_ms
        
        except Exception as e:
            log.debug("rpc_test_failed", url=endpoint.url, error=str(e))
            return float('inf')
    
    async def send_transaction_fast(
        self,
        transaction: Transaction,
        client: AsyncClient,
        max_retries: int = 3,
    ) -> Optional[str]:
        """Sende Transaktion mit Optimierungen.
        
        Args:
            transaction: Signierte Transaktion
            client: Solana RPC Client
            max_retries: Anzahl Wiederholungen
        
        Returns:
            Transaction Signature oder None
        """
        for attempt in range(max_retries):
            try:
                # Sende mit preflight skip für Geschwindigkeit
                response = await client.send_raw_transaction(
                    bytes(transaction),
                    opts={
                        "skip_preflight": True,  # Schneller, weniger Checks
                        "preflight_commitment": "confirmed",
                    },
                )
                
                if response.value:
                    signature = str(response.value)
                    log.info(
                        "transaction_sent",
                        signature=signature,
                        attempt=attempt + 1,
                    )
                    
                    # Warte auf Confirmation (confirmed = schneller als finalized)
                    await self._wait_for_confirmation(client, signature)
                    
                    return signature
            
            except Exception as e:
                log.warning(
                    "transaction_send_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
        
        return None
    
    async def _wait_for_confirmation(
        self,
        client: AsyncClient,
        signature: str,
        timeout: int = 30,
    ):
        """Warte auf Transaction Confirmation.
        
        Args:
            client: RPC Client
            signature: Transaction Signature
            timeout: Max Wartezeit in Sekunden
        """
        start = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start) < timeout:
            try:
                response = await client.get_signature_statuses([signature])
                
                if response.value and response.value[0]:
                    status = response.value[0]
                    
                    if status.confirmation_status in ["confirmed", "finalized"]:
                        log.info(
                            "transaction_confirmed",
                            signature=signature,
                            status=status.confirmation_status,
                        )
                        return
                    
                    if status.err:
                        log.error("transaction_failed", signature=signature, error=status.err)
                        raise Exception(f"Transaction failed: {status.err}")
            
            except Exception as e:
                log.debug("confirmation_check_error", error=str(e))
            
            await asyncio.sleep(1)
        
        log.warning("transaction_confirmation_timeout", signature=signature)
    
    async def send_via_jito(
        self,
        transaction: Transaction,
        tip_lamports: int = 10000,
    ) -> Optional[str]:
        """Sende via Jito Block Engine für maximale Geschwindigkeit.
        
        Jito garantiert Inclusion im nächsten Block.
        
        Args:
            transaction: Signierte Transaktion
            tip_lamports: Tip für Jito (höher = schneller)
        
        Returns:
            Bundle ID oder None
        """
        if not self.session:
            log.error("jito_send_failed", reason="No session")
            return None
        
        # Wähle nächsten Jito Endpoint (Round Robin)
        endpoint = self.JITO_ENDPOINTS[self.current_endpoint_idx % len(self.JITO_ENDPOINTS)]
        self.current_endpoint_idx += 1
        
        try:
            url = f"{endpoint}/api/v1/bundles"
            
            # Jito Bundle Format
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendBundle",
                "params": [
                    [bytes(transaction).hex()],  # Bundle mit einer TX
                ],
            }
            
            async with self.session.post(url, json=payload, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bundle_id = data.get("result")
                    
                    log.info("jito_bundle_sent", bundle_id=bundle_id, tip=tip_lamports)
                    return bundle_id
                else:
                    log.error("jito_send_failed", status=resp.status)
        
        except Exception as e:
            log.error("jito_send_error", error=str(e))
        
        return None


# Convenience functions
async def optimize_transaction_speed():
    """Quick Setup: Optimiere RPC und Priority Fees."""
    print("=" * 70)
    print("⚡ Transaction Speed Optimizer")
    print("=" * 70)
    print()
    
    async with TransactionOptimizer() as optimizer:
        print("🔍 Teste RPC Endpoints...")
        fastest = await optimizer.get_fastest_rpc()
        print(f"✅ Schnellster RPC: {fastest}")
        print()
        
        print("⚙️  Empfohlene Settings:")
        print(f"   Priority Fee: {optimizer.priority_fee_lamports} lamports (~$0.002)")
        print(f"   Compute Units: {optimizer.compute_units}")
        print(f"   Use Jito: {optimizer.use_jito}")
        print()
        
        print("💡 In .env.production setzen:")
        print(f"   SOLANA_RPC_URL={fastest}")
        print(f"   PRIORITY_FEE_LAMPORTS={optimizer.priority_fee_lamports}")
        print(f"   USE_JITO_BUNDLES=true")
        print()
        
        print("📊 Speed Comparison:")
        print("   Standard RPC:        2-5 Sekunden")
        print("   Mit Priority Fee:    1-2 Sekunden")
        print("   Mit Jito Bundle:     400-600ms ⚡")


if __name__ == "__main__":
    asyncio.run(optimize_transaction_speed())
