import asyncio
from typing import Optional, Dict
import inspect
import httpx
from solana.rpc.async_api import AsyncClient
from solana.rpc import commitment
from solana.rpc.providers import async_http
from solders.pubkey import Pubkey
from src.core.config import settings
from src.core.logger import log


def _ensure_httpx_proxy_compat() -> None:
    """Ensure the installed httpx AsyncClient accepts the kw 'proxy'.

    Some versions of `solana` pass `proxy=` to httpx.AsyncClient, but recent
    `httpx` uses `proxies=` instead. Detect this mismatch and monkeypatch the
    provider to use `proxies=` when necessary.
    """
    try:
        sig = inspect.signature(httpx.AsyncClient.__init__)
        # If httpx does not accept 'proxy' but accepts 'proxies', patch provider
        if 'proxy' not in sig.parameters and 'proxies' in sig.parameters:
            def _patched_init(self, endpoint: Optional[str] = None, extra_headers: Optional[Dict[str, str]] = None, timeout: float = async_http.DEFAULT_TIMEOUT, proxy: Optional[str] = None):
                super(async_http.AsyncHTTPProvider, self).__init__(endpoint, extra_headers)
                kwargs = {'timeout': timeout}
                if proxy is not None:
                    kwargs['proxies'] = proxy
                self.session = httpx.AsyncClient(**kwargs)

            async_http.AsyncHTTPProvider.__init__ = _patched_init
    except Exception:
        # If anything goes wrong, don't crash the client initialization here.
        return

class SolanaClient:
    def __init__(self):
        self.rpc_url = settings.SOLANA_RPC_URL
        self.client: Optional[AsyncClient] = None
        self._logger = log.bind(module="blockchain_client")

    async def connect(self):
        try:
            # Ensure compatibility between installed `httpx` and `solana` provider
            _ensure_httpx_proxy_compat()

            # AsyncClient signature varies between solana versions; pass only the rpc url
            self.client = AsyncClient(self.rpc_url)
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
