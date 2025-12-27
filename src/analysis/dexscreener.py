"""DexScreener API Integration - Real-time token data."""

import asyncio
from typing import Dict, Optional
from urllib.parse import quote_plus
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
    
    async def get_trending_memecoins(self, limit: int = 10) -> list:
        """Get trending Memecoins von DexScreener.
        
        Nutzt boosted + sorted by volume endpoint.
        
        Returns:
            List of token addresses (echte Memecoins!)
        """
        await self._ensure_session()
        
        try:
            # DexScreener: Search mit "pump" filter für Memecoins
            queries = [
                "pump",
                "pumpfun",
                "pump.fun",
                "inu",
                "pepe",
            ]
            endpoints = [f"{self.BASE_URL}/search?q={quote_plus(q)}" for q in queries]
            
            all_pairs = []
            
            for endpoint in endpoints:
                try:
                    async with self.session.get(endpoint, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            pairs = data.get('pairs', [])
                            all_pairs.extend(pairs)
                except:
                    continue
            
            if not all_pairs:
                self._logger.warning("no_memecoin_pairs_found")
                return []
            
            # Filter für Solana + echte Memecoins
            memecoin_candidates = []
            seen_addresses = set()
            
            for pair in all_pairs:
                # Nur Solana Chain
                if pair.get('chainId') != 'solana':
                    continue
                
                name = pair.get('baseToken', {}).get('name', '').lower()
                symbol = pair.get('baseToken', {}).get('symbol', '').lower()
                liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                volume_24h = float(pair.get('volume', {}).get('h24', 0))
                token_address = pair.get('baseToken', {}).get('address')

                url = (pair.get('url') or '').lower()
                dex_id = (pair.get('dexId') or '').lower()
                labels = pair.get('labels') or []
                labels_lower = [str(l).lower() for l in labels]

                is_pumpfun = (
                    'pump.fun' in url
                    or dex_id in {'pumpfun', 'pump.fun', 'pumpswap'}
                    or any('pumpfun' in l or 'pump.fun' in l for l in labels_lower)
                )
                
                # Skip bekannte tokens
                skip_names = ['sol', 'usdt', 'usdc']
                if any(skip in name for skip in skip_names):
                    continue
                
                # Memecoin criteria
                if (liquidity >= 5000 and 
                    volume_24h >= 500 and 
                    token_address and 
                    token_address not in seen_addresses):
                    
                    seen_addresses.add(token_address)
                    memecoin_candidates.append({
                        'address': token_address,
                        'name': pair.get('baseToken', {}).get('name'),
                        'symbol': symbol.upper(),
                        'liquidity': liquidity,
                        'volume': volume_24h,
                        'score': volume_24h * (1.2 if is_pumpfun else 1.0),
                    })
                    
                    self._logger.info("🎯 memecoin_found",
                                    name=pair.get('baseToken', {}).get('name'),
                                    symbol=symbol.upper(),
                                    liquidity=f"${liquidity:,.0f}",
                                    volume=f"${volume_24h:,.0f}",
                                    pumpfun=is_pumpfun)
            
            # Sort by score (volume, with slight pump.fun boost)
            memecoin_candidates.sort(key=lambda x: x['score'], reverse=True)
            
            return [m['address'] for m in memecoin_candidates[:limit]]
                
        except Exception as e:
            self._logger.error("trending_memecoins_error", error=str(e))
            return []

dexscreener = DexScreenerClient()
dex_analyzer = dexscreener  # Alias für Kompatibilität
