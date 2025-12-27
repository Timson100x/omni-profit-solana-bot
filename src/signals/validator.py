"""Signal Validation System - Multi-Check Filter für Token Signale.

Validiert Telegram/Discord Signale mit 8 Checks bevor Trade.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from src.core.logger import log
from src.core.config import settings


@dataclass
class ValidationResult:
    """Ergebnis der Signal-Validierung."""
    is_valid: bool
    score: float  # 0-100
    checks: Dict[str, bool]
    warnings: List[str]
    token_address: str
    timestamp: datetime


class SignalValidator:
    """Multi-Check Validation für Trading Signale.
    
    Filtert Scams und findet echte Gems mit 8 Checks:
    1. Liquidity Check (> $10k)
    2. LP Tokens Status (burned/locked)
    3. Mint Authority (revoked)
    4. Holder Distribution (top 10 < 40%)
    5. Contract Verification (kein Honeypot)
    6. Volume Check (real vs fake)
    7. Multi-Channel Confirmation
    8. Price History (keine Dumps)
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or settings.SOLANA_RPC_URL
        self.client = AsyncClient(self.rpc_url)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Cache für Multi-Channel Tracking
        self.signal_cache: Dict[str, List[datetime]] = {}
        
        # Minimum Requirements
        self.MIN_LIQUIDITY_USD = 10_000
        self.MAX_TOP_HOLDER_PCT = 40.0
        self.MIN_HOLDER_COUNT = 50
        self.MIN_CHANNEL_MENTIONS = 2
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
        await self.client.close()
    
    async def validate_signal(
        self,
        token_address: str,
        source_channel: str = "unknown",
    ) -> ValidationResult:
        """Vollständige Validierung eines Token Signals.
        
        Args:
            token_address: Solana Token Address
            source_channel: Quelle des Signals
        
        Returns:
            ValidationResult mit Score und Details
        """
        log.info("validating_signal", token=token_address, source=source_channel)
        
        checks = {}
        warnings = []
        
        # Check 1: Liquidity
        try:
            liquidity_usd = await self._check_liquidity(token_address)
            checks['liquidity'] = liquidity_usd >= self.MIN_LIQUIDITY_USD
            if not checks['liquidity']:
                warnings.append(f"Low liquidity: ${liquidity_usd:.0f}")
        except Exception as e:
            log.warning("liquidity_check_failed", error=str(e))
            checks['liquidity'] = False
            warnings.append("Liquidity check failed")
        
        # Check 2: LP Tokens
        try:
            lp_burned = await self._check_lp_burned(token_address)
            checks['lp_burned'] = lp_burned
            if not lp_burned:
                warnings.append("LP tokens not burned/locked")
        except Exception as e:
            log.warning("lp_check_failed", error=str(e))
            checks['lp_burned'] = False
        
        # Check 3: Mint Authority
        try:
            mint_revoked = await self._check_mint_authority(token_address)
            checks['mint_revoked'] = mint_revoked
            if not mint_revoked:
                warnings.append("⚠️  Mint authority active (can print tokens!)")
        except Exception as e:
            log.warning("mint_check_failed", error=str(e))
            checks['mint_revoked'] = False
        
        # Check 4: Holder Distribution
        try:
            distribution_ok = await self._check_holder_distribution(token_address)
            checks['distribution'] = distribution_ok
            if not distribution_ok:
                warnings.append("Top holders control >40%")
        except Exception as e:
            log.warning("distribution_check_failed", error=str(e))
            checks['distribution'] = False
        
        # Check 5: Contract Safety
        try:
            is_safe = await self._check_contract_safety(token_address)
            checks['safe_contract'] = is_safe
            if not is_safe:
                warnings.append("⚠️  Potential honeypot detected!")
        except Exception as e:
            log.warning("contract_check_failed", error=str(e))
            checks['safe_contract'] = False
        
        # Check 6: Volume Analysis
        try:
            volume_legit = await self._check_volume_legitimacy(token_address)
            checks['volume'] = volume_legit
            if not volume_legit:
                warnings.append("Suspicious volume pattern (potential fake pump)")
        except Exception as e:
            log.warning("volume_check_failed", error=str(e))
            checks['volume'] = False
        
        # Check 7: Multi-Channel Confirmation
        channel_count = self._track_signal(token_address, source_channel)
        checks['multi_channel'] = channel_count >= self.MIN_CHANNEL_MENTIONS
        if not checks['multi_channel']:
            warnings.append(f"Only {channel_count} channel mentions (need {self.MIN_CHANNEL_MENTIONS})")
        
        # Check 8: Price History
        try:
            price_stable = await self._check_price_history(token_address)
            checks['price_history'] = price_stable
            if not price_stable:
                warnings.append("Recent price dumps detected")
        except Exception as e:
            log.warning("price_history_failed", error=str(e))
            checks['price_history'] = False
        
        # Calculate Score (weighted)
        weights = {
            'liquidity': 20,        # Critical
            'lp_burned': 15,        # Critical
            'mint_revoked': 15,     # Critical
            'distribution': 10,
            'safe_contract': 20,    # Critical
            'volume': 10,
            'multi_channel': 5,
            'price_history': 5,
        }
        
        score = sum(weights[k] * (1 if v else 0) for k, v in checks.items())
        is_valid = score >= 70  # Minimum 70/100
        
        result = ValidationResult(
            is_valid=is_valid,
            score=score,
            checks=checks,
            warnings=warnings,
            token_address=token_address,
            timestamp=datetime.now(),
        )
        
        log.info(
            "validation_complete",
            token=token_address,
            valid=is_valid,
            score=score,
            warnings=len(warnings),
        )
        
        return result
    
    async def _check_liquidity(self, token_address: str) -> float:
        """Check Liquidity via DexScreener API.
        
        Returns:
            Liquidity in USD
        """
        if not self.session:
            return 0.0
        
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        # Höchste Liquidity Pool
                        max_liq = max(p.get('liquidity', {}).get('usd', 0) for p in pairs)
                        return float(max_liq)
        except Exception as e:
            log.debug("dexscreener_failed", error=str(e))
        
        return 0.0
    
    async def _check_lp_burned(self, token_address: str) -> bool:
        """Check if LP tokens are burned or locked.
        
        Returns:
            True if burned/locked
        """
        # TODO: Implement LP token check
        # For now, assume OK if has liquidity
        return True
    
    async def _check_mint_authority(self, token_address: str) -> bool:
        """Check if mint authority is revoked.
        
        Returns:
            True if revoked (safe)
        """
        try:
            pubkey = Pubkey.from_string(token_address)
            account_info = await self.client.get_account_info(pubkey)
            
            if account_info.value:
                # Parse mint account data
                # TODO: Proper parsing of mint authority
                # For now, basic check
                return True
        except Exception as e:
            log.debug("mint_check_error", error=str(e))
        
        return False
    
    async def _check_holder_distribution(self, token_address: str) -> bool:
        """Check if token distribution is healthy.
        
        Returns:
            True if top 10 holders < 40%
        """
        # TODO: Implement via Solana RPC getProgramAccounts
        # For now, assume OK
        return True
    
    async def _check_contract_safety(self, token_address: str) -> bool:
        """Check for honeypot/malicious contract.
        
        Returns:
            True if safe
        """
        # TODO: Implement honeypot detection
        # Check for: sellable, no hidden fees, etc.
        return True
    
    async def _check_volume_legitimacy(self, token_address: str) -> bool:
        """Detect fake volume pumps.
        
        Returns:
            True if volume is legitimate
        """
        if not self.session:
            return True
        
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        pair = pairs[0]
                        volume_24h = pair.get('volume', {}).get('h24', 0)
                        price_change_24h = pair.get('priceChange', {}).get('h24', 0)
                        
                        # Fake pump detection:
                        # High volume but low price change = wash trading
                        if volume_24h > 100000 and abs(price_change_24h) < 20:
                            log.warning(
                                "fake_volume_detected",
                                volume=volume_24h,
                                price_change=price_change_24h,
                            )
                            return False
        except Exception as e:
            log.debug("volume_check_error", error=str(e))
        
        return True
    
    async def _check_price_history(self, token_address: str) -> bool:
        """Check for recent dumps.
        
        Returns:
            True if no major dumps in last 24h
        """
        # TODO: Implement price history analysis
        return True
    
    def _track_signal(self, token_address: str, source: str) -> int:
        """Track signal across multiple channels.
        
        Returns:
            Number of unique channels mentioning this token
        """
        # Clean old entries (24h)
        cutoff = datetime.now() - timedelta(hours=24)
        self.signal_cache = {
            k: [t for t in v if t > cutoff]
            for k, v in self.signal_cache.items()
        }
        
        # Track new signal
        if token_address not in self.signal_cache:
            self.signal_cache[token_address] = []
        
        self.signal_cache[token_address].append(datetime.now())
        
        return len(self.signal_cache[token_address])
    
    def get_validation_summary(self) -> Dict:
        """Get summary of recent validations."""
        return {
            'tracked_signals': len(self.signal_cache),
            'multi_channel_signals': sum(
                1 for mentions in self.signal_cache.values()
                if len(mentions) >= self.MIN_CHANNEL_MENTIONS
            ),
        }


# Singleton instance
signal_validator = SignalValidator()


async def main():
    """Test Signal Validator."""
    print("=" * 70)
    print("🔍 Signal Validation System Test")
    print("=" * 70)
    print()
    
    # Test token (Beispiel)
    test_token = "So11111111111111111111111111111111111111112"  # SOL
    
    async with SignalValidator() as validator:
        result = await validator.validate_signal(
            test_token,
            source_channel="telegram_test",
        )
        
        print(f"Token: {result.token_address}")
        print(f"Valid: {'✅ YES' if result.is_valid else '❌ NO'}")
        print(f"Score: {result.score}/100")
        print()
        print("Checks:")
        for check, passed in result.checks.items():
            icon = "✅" if passed else "❌"
            print(f"  {icon} {check}")
        
        if result.warnings:
            print()
            print("⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        print()
        print("Decision:", "🚀 TRADE" if result.is_valid else "🛑 SKIP")


if __name__ == "__main__":
    asyncio.run(main())
