import asyncio
from typing import Optional
from solana.rpc.async_api import AsyncClient
from solana.rpc import commitment
from solders.pubkey import Pubkey
from src.core.config import settings
from src.core.logger import log

class SolanaClient:
    def __init__(self):
        self.rpc_url = settings.SOLANA_RPC_URL
        self.client: Optional[AsyncClient] = None
        self._logger = log.bind(module="blockchain_client")

    async def connect(self):
        try:
            self.client = AsyncClient(self.rpc_url, commitment=commitment.Confirmed)
            self._logger.info("✅ Verbunden mit Solana RPC", url=self.rpc_url)
        except Exception as e:
            self._logger.error("RPC-Fehler", error=str(e))
            raise e

    async def close(self):
        if self.client:
            await self.client.close()

    async def get_balance(self, pubkey_str: str) -> float:
        if not self.client:
            await self.connect()
        try:
            pubkey = Pubkey.from_string(pubkey_str)
            response = await self.client.get_balance(pubkey)
            return response.value / 1_000_000_000
        except Exception as e:
            self._logger.error("Balance Error", error=str(e))
            return 0.0

solana_client = SolanaClient()
