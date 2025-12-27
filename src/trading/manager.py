"""Trade Manager - Executes and monitors trades."""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from src.core.config import settings
from src.core.logger import log
from src.blockchain.wallet import wallet_manager
from src.blockchain.client import solana_client
from src.blockchain.transaction_optimizer import TransactionOptimizer

@dataclass
class Position:
    token_address: str
    token_name: str
    entry_price: float
    amount_sol: float
    target_multiplier: float
    stop_loss_pct: float
    entry_time: datetime
    status: str = "open"  # open, closed, stopped

class TradeManager:
    def __init__(self):
        self._logger = log.bind(module="trade_manager")
        self.positions: List[Position] = []
        self.daily_loss_sol: float = 0.0
        self.trades_today: int = 0
        
        # Initialize Transaction Optimizer with MEV Protection
        self.tx_optimizer = TransactionOptimizer(
            use_jito=True,  # Anti-MEV via Jito Bundles
            priority_fee_lamports=10000,  # Fast inclusion
            compute_units=200_000
        )
        self._logger.info("trade_manager_initialized", mev_protection=True)

    async def _calculate_trade_size(self, confidence: float) -> float:
        """Calculate trade size.

        If `settings.TRADE_BALANCE_FRACTION` is set, use wallet balance sizing
        ("reinvest"), keeping `settings.MIN_SOL_RESERVE` aside for fees.
        Otherwise fall back to the legacy MIN/MAX sizing.
        """
        fraction = getattr(settings, "TRADE_BALANCE_FRACTION", None)
        if fraction is None:
            return settings.MIN_TRADE_SIZE_SOL + (
                (settings.MAX_TRADE_SIZE_SOL - settings.MIN_TRADE_SIZE_SOL) * confidence
            )

        try:
            pubkey = wallet_manager.get_public_key()
            balance = await solana_client.get_balance(pubkey)
        except Exception:
            balance = 0.0

        reserve = float(getattr(settings, "MIN_SOL_RESERVE", 0.02) or 0.0)
        committed = sum(
            p.amount_sol for p in self.positions if p.status == "open"
        )
        available = max(0.0, balance - reserve - committed)
        trade_size = max(0.0, available * float(fraction))
        return trade_size
        
    async def execute_trade(self, token_data: Dict, analysis: Dict) -> bool:
        """Execute a buy trade"""
        
        # Safety checks
        if settings.EMERGENCY_STOP:
            self._logger.error("trade_blocked_emergency_stop")
            return False
        
        if not settings.ALLOW_REAL_TRANSACTIONS:
            self._logger.warning("trade_simulation_mode", token=token_data['name'])
            return await self._simulate_trade(token_data, analysis)
        
        # Check daily loss limit
        if self.daily_loss_sol >= settings.MAX_DAILY_LOSS_SOL:
            self._logger.error("daily_loss_limit_reached", loss=self.daily_loss_sol)
            return False
        
        # Determine trade size based on confidence
        confidence = analysis.get('confidence', 0.5)
        trade_size = await self._calculate_trade_size(confidence)

        if trade_size <= 0:
            self._logger.warning(
                "trade_size_too_small",
                token=token_data.get('name'),
                confidence=confidence,
            )
            return False
        
        self._logger.info("executing_trade",
                         token=token_data['name'],
                         size_sol=trade_size,
                         confidence=confidence)
        
        try:
            # 🚀 LIVE MEMECOIN TRADING - Kaufe echte Tokens
            from src.trading.simple_swapper import jupiter_swapper
            
            # SOL -> Memecoin Token swap
            success = await jupiter_swapper.swap_sol_to_token(
                token_address=token_data['address'],
                amount_sol=trade_size,
                slippage_bps=int(settings.SLIPPAGE_TOLERANCE * 10000),
            )
            
            if not success:
                self._logger.error("memecoin_swap_failed", token=token_data['name'])
                return False
            
            # Create position tracking for AUTO-SELL
            position = Position(
                token_address=token_data['address'],
                token_name=token_data['name'],
                entry_price=token_data['price_usd'],
                amount_sol=trade_size,
                target_multiplier=analysis.get('target_multiplier', 2.0),
                stop_loss_pct=0.30,  # Auto-sell bei -30%
                entry_time=datetime.now()
            )
            
            self.positions.append(position)
            self.trades_today += 1
            
            self._logger.info("✅ memecoin_bought",
                            token=token_data['name'],
                            amount_sol=trade_size,
                            position_count=len(self.positions))
            
            self._logger.info("✅ rsol_staked",
                            signal=token_data['name'][:20],
                            amount_sol=trade_size,
                            position_count=len(self.positions))
            
            return True
            
        except Exception as e:
            self._logger.error("trade_execution_failed", error=str(e))
            return False
    
    async def _simulate_trade(self, token_data: Dict, analysis: Dict) -> bool:
        """Simulate trade execution"""
        confidence = analysis.get('confidence', 0.5)
        trade_size = await self._calculate_trade_size(confidence)

        if trade_size <= 0:
            self._logger.warning(
                "trade_size_too_small",
                token=token_data.get('name'),
                confidence=confidence,
            )
            return False
        
        self._logger.info("📊 trade_simulated",
                         token=token_data['name'],
                         size_sol=trade_size,
                         confidence=confidence,
                         reason=analysis.get('reason'))
        
        # Create simulated position
        position = Position(
            token_address=token_data['address'],
            token_name=token_data['name'],
            entry_price=token_data['price_usd'],
            amount_sol=trade_size,
            target_multiplier=analysis.get('target_multiplier', 2.0),
            stop_loss_pct=settings.STOP_LOSS_PCT,
            entry_time=datetime.now(),
            status="simulated"
        )
        
        self.positions.append(position)
        return True
    
    async def monitor_positions(self):
        """Monitor open positions for take-profit/stop-loss"""
        if not self.positions:
            return
        
        open_positions = [p for p in self.positions if p.status == "open"]
        if not open_positions:
            return
        
        self._logger.info("monitoring_positions", count=len(open_positions))
        
        # Check each position for exit conditions
        from src.analysis.dexscreener import dexscreener
        
        for position in open_positions:
            try:
                # Get current price
                token_data = await dexscreener.get_token_data(position.token_address)
                
                if not token_data:
                    continue
                
                current_price = token_data['price_usd']
                price_change = (current_price - position.entry_price) / position.entry_price
                
                self._logger.debug("position_check",
                                 token=position.token_name,
                                 entry_price=position.entry_price,
                                 current_price=current_price,
                                 change_pct=f"{price_change*100:.1f}%")
                
                # Take Profit: Reached target multiplier
                if current_price >= position.entry_price * position.target_multiplier:
                    self._logger.info("🎯 take_profit_triggered",
                                    token=position.token_name,
                                    profit_pct=f"{price_change*100:.1f}%")
                    await self._exit_position(position, "take_profit", current_price)
                
                # Stop Loss: Down 30%
                elif price_change <= -position.stop_loss_pct:
                    self._logger.warning("🛑 stop_loss_triggered",
                                       token=position.token_name,
                                       loss_pct=f"{price_change*100:.1f}%")
                    await self._exit_position(position, "stop_loss", current_price)
                    
            except Exception as e:
                self._logger.error("position_monitoring_error",
                                 token=position.token_name,
                                 error=str(e))
    
    async def _exit_position(self, position: Position, reason: str, exit_price: float):
        """Exit a position (sell tokens) - AUTO SELL"""
        try:
            # Calculate P&L
            price_change = (exit_price - position.entry_price) / position.entry_price
            pnl_sol = position.amount_sol * price_change
            
            if reason == "stop_loss":
                self.daily_loss_sol += abs(pnl_sol)
            
            # 🚀 EXECUTE SELL via Jupiter
            from src.trading.simple_swapper import jupiter_swapper
            
            # Token -> SOL swap (estimate token amount)
            token_amount_estimate = int(position.amount_sol * 1e9)  # Rough estimate
            
            sell_success = await jupiter_swapper.swap_token_to_sol(
                token_address=position.token_address,
                token_amount=token_amount_estimate,
                slippage_bps=1000,  # 10% for exit
            )
            
            if sell_success:
                self._logger.info("💰 position_sold",
                                token=position.token_name,
                                reason=reason,
                                pnl_sol=f"{pnl_sol:.4f}",
                                pnl_pct=f"{price_change*100:.1f}%")
            else:
                self._logger.error("sell_failed_keeping_position",
                                 token=position.token_name)
                return
            
            # Update position
            position.status = "closed"
            
        except Exception as e:
            self._logger.error("exit_position_failed",
                             token=position.token_name,
                             error=str(e))
    
    def get_position_summary(self) -> Dict:
        """Get summary of all positions"""
        open_positions = [p for p in self.positions if p.status == "open"]
        closed_positions = [p for p in self.positions if p.status == "closed"]
        
        return {
            'total_positions': len(self.positions),
            'open_positions': len(open_positions),
            'closed_positions': len(closed_positions),
            'daily_loss_sol': self.daily_loss_sol,
            'trades_today': self.trades_today
        }

trade_manager = TradeManager()
