"""DexScreener API Integration - Real-time token data."""

import asyncio
from typing import Dict, Optional
import aiohttp
from src.core.logger import log

class DexScreenerClient:
    BASE_URL = "https://api.dexscreener.com/latest/dex"
    
    def __init__(self):
        self._logger = log.bind(module="dexscreener")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_token_data(self, token_address: str) -> Optional[Dict]:
        """Get token data from DexScreener"""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/tokens/{token_address}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    self._logger.warning("dexscreener_error", 
                                       status=response.status,
                                       token=token_address)
                    return None
                
                data = await response.json()
                
                if not data or 'pairs' not in data or not data['pairs']:
                    self._logger.warning("no_pairs_found", token=token_address)
                    return None
                
                # Get the pair with highest liquidity
                pair = max(data['pairs'], key=lambda p: float(p.get('liquidity', {}).get('usd', 0)))
                
                parsed = {
                    'address': token_address,
                    'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                    'symbol': pair.get('baseToken', {}).get('symbol', 'Unknown'),
                    'price_usd': float(pair.get('priceUsd', 0)),
                    'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                    'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                    'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                    'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0)),
                    'txns_24h': pair.get('txns', {}).get('h24', {}),
                    'dex': pair.get('dexId', 'unknown'),
                    'pair_address': pair.get('pairAddress', ''),
                }
                
                self._logger.info("token_data_fetched",
                                token=parsed['name'],
                                liquidity=parsed['liquidity'],
                                volume=parsed['volume_24h'])
                
                return parsed
                
        except asyncio.TimeoutError:
            self._logger.error("dexscreener_timeout", token=token_address)
            return None
        except Exception as e:
            self._logger.error("dexscreener_exception", error=str(e), token=token_address)
            return None
    
    async def search_tokens(self, query: str) -> list:
        """Search for tokens by name or symbol"""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/search?q={query}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                return data.get('pairs', [])
                
        except Exception as e:
            self._logger.error("search_failed", error=str(e))
            return []

dexscreener = DexScreenerClient()
