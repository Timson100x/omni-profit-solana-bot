"""Signal Processor - Aggregates and validates signals from multiple sources."""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from src.core.logger import log
from src.analysis.gmgn import gmgn_client

@dataclass
class Signal:
    source: str  # telegram, discord, twitter
    token_address: str
    token_name: str
    confidence: float  # 0.0 - 1.0
    timestamp: datetime
    metadata: Dict

class SignalProcessor:
    def __init__(self):
        self._logger = log.bind(module="signal_processor")
        self.signals_queue: List[Signal] = []
        
    async def collect_signals(self) -> List[Signal]:
        """Collect signals from all sources"""
        signals = []
        
        # DexScreener trending tokens (LIVE)
        dexscreener_signals = await self._collect_dexscreener()
        signals.extend(dexscreener_signals)
        
        # Telegram signals (future enhancement)
        # telegram_signals = await self._collect_telegram()
        # signals.extend(telegram_signals)
        
        # Discord signals (future enhancement)
        # discord_signals = await self._collect_discord()
        # signals.extend(discord_signals)
        
        self._logger.info("signals_collected", count=len(signals))
        return signals
    
    async def _collect_dexscreener(self) -> List[Signal]:
        """Collect trending tokens from DexScreener API"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Korrigierte URL: Trending Solana Pairs
                url = "https://api.dexscreener.com/latest/dex/search?q=solana"
                
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        self._logger.warning("dexscreener_api_error", status=response.status)
                        return []
                    
                    data = await response.json()
                    
                    # Prüfe ob pairs existieren
                    if not data or 'pairs' not in data:
                        self._logger.warning("dexscreener_no_data")
                        return []
                    
                    pairs = data.get('pairs', [])
                    
                    if not pairs:
                        self._logger.info("dexscreener_no_pairs")
                        return []
                    
                    # Filter: Solana tokens mit Liquidität > $10k
                    solana_pairs = [
                        p for p in pairs
                        if p.get('chainId') == 'solana'
                        and float(p.get('liquidity', {}).get('usd', 0)) > 10000
                    ]
                    
                    # Sortiere nach 24h Volumen
                    solana_pairs.sort(
                        key=lambda p: float(p.get('volume', {}).get('h24', 0)),
                        reverse=True
                    )
                    
                    # Top 3 trending tokens
                    signals = []
                    for pair in solana_pairs[:3]:
                        token = pair.get('baseToken', {})
                        if not token or not token.get('address'):
                            continue
                            
                        signal = Signal(
                            source='dexscreener',
                            token_address=token.get('address', ''),
                            token_name=token.get('name', 'Unknown'),
                            confidence=0.7,  # DexScreener = reliable source
                            timestamp=datetime.now(),
                            metadata={
                                'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
                                'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                                'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                            }
                        )
                        signals.append(signal)
                    
                    self._logger.info("dexscreener_signals", count=len(signals))
                    return signals
                    
        except Exception as e:
            self._logger.error("dexscreener_collection_failed", error=str(e))
            return []
    
    async def _collect_telegram(self) -> List[Signal]:
        """Telegram signal collection - Future enhancement"""
        return []
    
    async def _collect_discord(self) -> List[Signal]:
        """Discord signal collection - Future enhancement"""
        return []
    
    async def _collect_twitter(self) -> List[Signal]:
        """Twitter signal collection - Future enhancement"""
        return []
    
    def validate_signal(self, signal: Signal) -> bool:
        """Validate signal quality and confidence threshold"""
        if signal.confidence < 0.5:
            self._logger.debug("signal_rejected_low_confidence", signal=signal.token_name)
            return False
        
        if not signal.token_address or len(signal.token_address) < 32:
            self._logger.debug("signal_rejected_invalid_address", signal=signal.token_name)
            return False
        
        return True
    
    def aggregate_signals(self, signals: List[Signal]) -> List[Signal]:
        """Aggregate multiple signals for same token"""
        token_map: Dict[str, List[Signal]] = {}
        
        for signal in signals:
            if signal.token_address not in token_map:
                token_map[signal.token_address] = []
            token_map[signal.token_address].append(signal)
        
        aggregated = []
        for token_addr, token_signals in token_map.items():
            # Average confidence from multiple sources
            avg_confidence = sum(s.confidence for s in token_signals) / len(token_signals)
            
            # Take most recent signal as base
            latest = max(token_signals, key=lambda s: s.timestamp)
            latest.confidence = avg_confidence
            latest.metadata['signal_count'] = len(token_signals)
            
            aggregated.append(latest)
        
        return aggregated

signal_processor = SignalProcessor()
