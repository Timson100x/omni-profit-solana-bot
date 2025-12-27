#!/usr/bin/env python3
"""Complete Trading Bot mit allen Advanced Features.

Features:
- MEV Protection via Jito
- Signal Validation System
- Discord Server Monitor
- Liquidity Sniper
- Transaction Speed Optimization
"""

import asyncio
import sys
from datetime import datetime

from src.core.logger import log
from src.core.config import settings
from src.signals.processor import signal_processor
from src.signals.validator import signal_validator
from src.ai.agent import ai_agent
from src.analysis.dexscreener import dex_analyzer
from src.trading.manager import trade_manager
from src.monitoring.notifier import notifier
from src.social.discord_monitor import run_discord_bot
from src.trading.liquidity_sniper import run_sniper


async def initialize_components():
    """Initialize all bot components."""
    log.info("system_initializing")
    
    print("=" * 70)
    print("🚀 Omni Profit Bot - Advanced Edition")
    print("=" * 70)
    print()
    
    # Check config
    print("⚙️  Configuration:")
    print(f"   Network: Solana {'Mainnet' if 'mainnet' in settings.SOLANA_RPC_URL else 'Devnet'}")
    print(f"   Real Trades: {'✅ YES' if settings.ALLOW_REAL_TRANSACTIONS else '❌ NO (Simulation)'}")
    print(f"   Emergency Stop: {'🛑 YES' if settings.EMERGENCY_STOP else '✅ NO'}")
    print()
    
    # Advanced Features
    print("🔥 Advanced Features:")
    print(f"   ✅ MEV Protection (Jito Bundles)")
    print(f"   ✅ Signal Validation (8 Checks)")
    print(f"   ✅ Transaction Speed Optimizer")
    print(f"   ✅ Discord Server Monitor: {'✅' if settings.DISCORD_BOT_TOKEN else '❌'}")
    print(f"   ✅ Liquidity Sniper (WebSocket)")
    print()
    
    # Integrations
    print("🔌 Integrations:")
    print(f"   Gemini AI: {'✅' if settings.GEMINI_API_KEY else '❌'}")
    print(f"   Telegram: {'✅' if settings.TELEGRAM_API_ID else '❌'}")
    print(f"   Discord: {'✅' if settings.DISCORD_BOT_TOKEN else '❌'}")
    print()
    
    # Wallet
    if settings.WALLET_PRIVATE_KEY:
        from src.blockchain.wallet import wallet_manager
        wallet_manager.load_wallet()
        pubkey = wallet_manager.get_public_key()
        print(f"💰 Wallet: {pubkey[:8]}...{pubkey[-8:]}")
        
        # Get balance
        from src.blockchain.client import solana_client
        try:
            balance_lamports = await solana_client.get_balance()
            balance_sol = balance_lamports / 1e9
            print(f"💵 Balance: {balance_sol:.6f} SOL")
        except:
            print(f"💵 Balance: Unable to fetch")
    else:
        print("⚠️  No wallet configured")
    
    print()
    log.info("system_ready")


async def run_trading_loop():
    """Main trading loop - Collect signals, analyze, trade."""
    log.info("trading_loop_starting")
    
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            log.info("trading_loop_iteration", count=loop_count)
            
            # 1. Collect signals
            signals = await signal_processor.collect_signals()
            
            if signals:
                log.info("signals_collected", count=len(signals))
                print(f"\n📡 {len(signals)} signals collected")
                
                for signal in signals[:3]:  # Process top 3
                    print(f"\n🔍 Analyzing: {signal.token_name} ({signal.token_address[:8]}...)")
                    
                    # 2. Validate signal
                    validation = await signal_validator.validate_signal(
                        signal.token_address,
                        source_channel=signal.source,
                    )
                    
                    print(f"   Validation Score: {validation.score}/100")
                    
                    if not validation.is_valid:
                        print(f"   ❌ REJECTED - {validation.warnings[0] if validation.warnings else 'Low score'}")
                        continue
                    
                    # 3. Get market data
                    token_data = await dex_analyzer.get_token_data(signal.token_address)
                    
                    if not token_data:
                        print(f"   ❌ No market data")
                        continue
                    
                    print(f"   💰 Price: ${token_data['price_usd']:.6f}")
                    print(f"   💧 Liquidity: ${token_data.get('liquidity_usd', 0):,.0f}")
                    
                    # 4. AI Analysis
                    analysis = await ai_agent.analyze_token(
                        token_address=signal.token_address,
                        token_name=signal.token_name,
                        market_data=token_data,
                        signal_confidence=signal.confidence,
                    )
                    
                    print(f"   🤖 AI Score: {analysis.get('score', 0)}/100")
                    
                    if analysis.get('score', 0) < 70:
                        print(f"   ❌ AI rejected")
                        continue
                    
                    # 5. Execute trade with MEV protection
                    print(f"   🚀 Executing trade with Jito protection...")
                    
                    success = await trade_manager.execute_trade(token_data, analysis)
                    
                    if success:
                        print(f"   ✅ TRADE EXECUTED")
                        
                        # Notify
                        await notifier.send_trade_notification(
                            token_name=signal.token_name,
                            action="BUY",
                            amount_sol=0.05,
                            price=token_data['price_usd'],
                        )
                    else:
                        print(f"   ❌ Trade failed")
            
            # 6. Monitor positions
            await trade_manager.monitor_positions()
            
            # Sleep
            print(f"\n💤 Sleeping 60s... (Loop #{loop_count})")
            await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            log.info("trading_loop_interrupted")
            break
        
        except Exception as e:
            log.error("trading_loop_error", error=str(e), loop=loop_count)
            print(f"\n❌ Error in trading loop: {e}")
            await asyncio.sleep(60)


async def run_discord_monitor():
    """Run Discord server monitor."""
    if not settings.DISCORD_BOT_TOKEN:
        log.info("discord_monitor_disabled")
        return
    
    try:
        await run_discord_bot()
    except Exception as e:
        log.error("discord_monitor_error", error=str(e))


async def run_liquidity_sniper():
    """Run liquidity sniper."""
    # Optional: Enable with env var
    enable_sniper = False  # Set to True to enable
    
    if not enable_sniper:
        return
    
    try:
        await run_sniper(dex="raydium")
    except Exception as e:
        log.error("sniper_error", error=str(e))


async def main():
    """Main entry point."""
    try:
        # Initialize
        await initialize_components()
        
        print("=" * 70)
        print("🎯 Bot gestartet!")
        print("=" * 70)
        print()
        print("Active Modules:")
        print("  ✅ Trading Loop (Signal → Validate → Trade)")
        print("  ✅ Position Monitoring")
        if settings.DISCORD_BOT_TOKEN:
            print("  ✅ Discord Server Monitor")
        print()
        print("Press Ctrl+C to stop")
        print()
        
        # Run all tasks
        tasks = [
            asyncio.create_task(run_trading_loop()),
        ]
        
        # Optional: Discord monitor
        if settings.DISCORD_BOT_TOKEN:
            tasks.append(asyncio.create_task(run_discord_monitor()))
        
        # Optional: Liquidity sniper
        # tasks.append(asyncio.create_task(run_liquidity_sniper()))
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping bot...")
        log.info("system_shutdown")
        
        # Show summary
        summary = trade_manager.get_position_summary()
        print("\n📊 Session Summary:")
        print(f"   Trades Today: {summary['trades_today']}")
        print(f"   Open Positions: {summary['open_positions']}")
        print(f"   Closed Positions: {summary['closed_positions']}")
        print()
        print("✅ Bot stopped cleanly")


if __name__ == "__main__":
    asyncio.run(main())
