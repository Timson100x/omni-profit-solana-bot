"""GMGN.ai API Integration - Faster Memecoin Data for Insiders.

GMGN ist schneller als DexScreener und hat bessere Insider-Daten.
"""

import asyncio
from typing import Dict, Optional, List
import aiohttp
from datetime import datetime
from src.core.logger import log


class GMGNClient:
    """GMGN.ai API Client für Solana Memecoins."""
    
    BASE_URL = "https://gmgn.ai/defi/quotation/v1"
    CHAIN = "sol"  # Solana
    
    def __init__(self):
        self._logger = log.bind(module="gmgn")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_trending_tokens(self, limit: int = 10) -> List[Dict]:
        """Get trending Solana tokens from GMGN.
        
        Args:
            limit: Number of tokens to return
            
        Returns:
            List of token data dicts
        """
        await self._ensure_session()
        
        try:
            # GMGN trending endpoint
            url = f"{self.BASE_URL}/tokens/top_gainers/{self.CHAIN}"
            params = {
                "limit": limit,
                "orderby": "volume_24h",  # Sort by 24h volume
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
            
            async with self.session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status != 200:
                    self._logger.warning("gmgn_error", status=response.status)
                    return []
                
                data = await response.json()
                
                if not data or 'data' not in data:
                    self._logger.warning("gmgn_no_data")
                    return []
                
                tokens = data['data'].get('tokens', [])
                
                self._logger.info("gmgn_trending_fetched", count=len(tokens))
                return tokens[:limit]
                
        except asyncio.TimeoutError:
            self._logger.error("gmgn_timeout")
            return []
        except Exception as e:
            self._logger.error("gmgn_exception", error=str(e))
            return []
    
    async def get_token_data(self, token_address: str) -> Optional[Dict]:
        """Get detailed token data from GMGN.
        
        Args:
            token_address: Solana token address
            
        Returns:
            Parsed token data or None
        """
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/tokens/{self.CHAIN}/{token_address}"
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    self._logger.warning("gmgn_token_error", 
                                       status=response.status,
                                       token=token_address)
                    return None
                
                data = await response.json()
                
                if not data or 'data' not in data:
                    self._logger.warning("gmgn_no_token_data", token=token_address)
                    return None
                
                token = data['data']
                
                # Parse to standardized format
                parsed = {
                    'address': token_address,
                    'name': token.get('name', 'Unknown'),
                    'symbol': token.get('symbol', 'Unknown'),
                    'price_usd': float(token.get('price', 0)),
                    'liquidity': float(token.get('liquidity', 0)),
                    'liquidity_usd': float(token.get('liquidity', 0)),
                    'volume_24h': float(token.get('volume_24h', 0)),
                    'price_change_24h': float(token.get('price_change_24h', 0)),
                    'price_change_1h': float(token.get('price_change_1h', 0)),
                    'market_cap': float(token.get('market_cap', 0)),
                    'holders': int(token.get('holder_count', 0)),
                    'created_at': token.get('created_timestamp', 0),
                    'is_verified': token.get('is_show_alert', False) == False,
                    'buy_count_24h': int(token.get('buy_24h', 0)),
                    'sell_count_24h': int(token.get('sell_24h', 0)),
                }
                
                self._logger.info("gmgn_token_fetched",
                                token=parsed['name'],
                                price=parsed['price_usd'],
                                liquidity=parsed['liquidity'])
                
                return parsed
                
        except asyncio.TimeoutError:
            self._logger.error("gmgn_token_timeout", token=token_address)
            return None
        except Exception as e:
            self._logger.error("gmgn_token_exception", error=str(e), token=token_address)
            return None
    
    async def get_new_tokens(self, hours: int = 1, min_liquidity: float = 5000) -> List[Dict]:
        """Get newly created tokens (insider advantage).
        
        Args:
            hours: Look back X hours
            min_liquidity: Minimum liquidity in USD
            
        Returns:
            List of new tokens
        """
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/tokens/new/{self.CHAIN}"
            params = {
                "period": f"{hours}h",
                "min_liquidity": min_liquidity,
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            }
            
            async with self.session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                tokens = data.get('data', {}).get('tokens', [])
                
                self._logger.info("gmgn_new_tokens_fetched", count=len(tokens))
                return tokens
                
        except Exception as e:
            self._logger.error("gmgn_new_tokens_exception", error=str(e))
            return []


# Global instance
gmgn_client = GMGNClient()
