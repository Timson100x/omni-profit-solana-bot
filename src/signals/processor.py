"""Signal Processor - Aggregates and validates signals from multiple sources."""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from src.core.logger import log

@dataclass
class Signal:
    source: str  # telegram, discord, dexscreener
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
        
        # DexScreener trending MEMECOINS (LIVE)
        dexscreener_signals = await self._collect_dexscreener()
        signals.extend(dexscreener_signals)
        
        self._logger.info("signals_collected", count=len(signals))
        return signals
    
    async def _collect_dexscreener(self) -> List[Signal]:
        """Collect ECHTE MEMECOINS from DexScreener API"""
        try:
            from src.analysis.dexscreener import dexscreener
            
            # Nutze neue Memecoin-Finder Methode
            memecoin_addresses = await dexscreener.get_trending_memecoins(limit=10)
            
            if not memecoin_addresses:
                self._logger.warning("no_memecoins_found")
                return []
            
            # Erstelle Signals für gefundene Memecoins
            signals = []
            
            for address in memecoin_addresses[:5]:  # Top 5 Memecoins
                # Get token data
                token_data = await dexscreener.get_token_data(address)
                
                if not token_data:
                    continue
                
                signal = Signal(
                    source="dexscreener",
                    token_address=address,
                    token_name=token_data.get('name', 'Unknown'),
                    confidence=0.7,  # Base confidence
                    timestamp=datetime.now(),
                    metadata={
                        'liquidity': token_data.get('liquidity', 0),
                        'volume_24h': token_data.get('volume_24h', 0),
                        'price_change_24h': token_data.get('price_change_24h', 0),
                    }
                )
                
                signals.append(signal)
            
            self._logger.info("dexscreener_signals", 
                            count=len(signals))
            
            return signals
            
        except Exception as e:
            self._logger.error("dexscreener_collection_error", error=str(e))
            return []

signal_processor = SignalProcessor()
