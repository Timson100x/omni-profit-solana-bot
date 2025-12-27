#!/usr/bin/env python3
"""
Omni-Profit Solana Trading Bot - Complete System
Integrates all components: signal monitoring, AI analysis, and trading execution
"""

import asyncio
import signal
import sys
from datetime import datetime
from src.core.logger import setup_logger, log
from src.core.config import settings

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(sig, frame):
    """Handle CTRL+C gracefully"""
    global shutdown_flag
    print("\n🛑 Shutdown signal received. Stopping bot...")
    shutdown_flag = True

async def initialize_components():
    """Initialize all bot components"""
    logger = log.bind(module="init")
    logger.info("🚀 Starting Omni-Profit Bot", env=settings.ENV)
    
    # Check safety settings
    if settings.EMERGENCY_STOP:
        logger.error("❌ EMERGENCY_STOP is enabled. Bot cannot start.")
        return False
    
    if not settings.ALLOW_REAL_TRANSACTIONS:
        logger.warning("⚠️ ALLOW_REAL_TRANSACTIONS is False - Bot will run in simulation mode")
    
    # Initialize blockchain client
    try:
        from src.blockchain.client import solana_client
        await solana_client.connect()
        logger.info("✅ Blockchain client connected", rpc=settings.SOLANA_RPC_URL)
    except Exception as e:
        logger.error("❌ Failed to connect to Solana RPC", error=str(e))
        return False
    
    # Initialize wallet
    try:
        if settings.WALLET_PRIVATE_KEY:
            from src.blockchain.wallet import wallet_manager
            wallet_manager.load_wallet()
            pubkey = wallet_manager.get_public_key()
            logger.info("✅ Wallet loaded", pubkey=pubkey)
            
            # Check balance
            balance = await solana_client.get_balance(pubkey)
            logger.info("💰 Wallet balance", sol=balance)
            
            if balance < settings.MIN_TRADE_SIZE_SOL:
                logger.warning("⚠️ Low wallet balance", balance=balance, min_required=settings.MIN_TRADE_SIZE_SOL)
        else:
            logger.warning("⚠️ No wallet configured - running in demo mode")
    except Exception as e:
        logger.warning("⚠️ Wallet not loaded", error=str(e))
        logger.info("💡 Bot will run in demo mode without wallet")
    
    # Initialize Jupiter client (DEX)
    try:
        from src.trading.jupiter_client import ping_jupiter
        if ping_jupiter():
            logger.info("✅ Jupiter DEX client reachable")
        else:
            logger.warning("⚠️ Jupiter API unreachable")
    except Exception as e:
        logger.warning("⚠️ Jupiter client check failed", error=str(e))
    
    # Initialize AI Agent
    try:
        from src.ai.agent import ai_agent
        if ai_agent.enabled:
            logger.info("✅ AI Agent (Gemini) initialized")
        else:
            logger.warning("⚠️ AI Agent unavailable - using fallback analysis")
    except Exception as e:
        logger.warning("⚠️ AI Agent initialization", error=str(e))
    
    # Initialize DexScreener client
    try:
        from src.analysis.dexscreener import dexscreener
        logger.info("✅ DexScreener client initialized")
    except Exception as e:
        logger.warning("⚠️ DexScreener initialization", error=str(e))
    
    logger.info("✅ All components initialized successfully")
    return True

async def run_trading_loop():
    """Main trading loop"""
    logger = log.bind(module="trading_loop")
    logger.info("🔄 Starting trading loop")
    
    # Import trading components
    from src.signals.processor import signal_processor
    from src.ai.agent import ai_agent
    from src.analysis.dexscreener import dexscreener
    from src.trading.manager import trade_manager
    
    iteration = 0
    while not shutdown_flag:
        try:
            iteration += 1
            logger.info("🔄 Trading loop iteration", iteration=iteration, time=datetime.now().isoformat())
            
            # Step 1: Collect signals from all sources
            signals = await signal_processor.collect_signals()
            
            if signals:
                logger.info("📡 signals_received", count=len(signals))
                
                # Step 2: Validate and aggregate signals
                valid_signals = [s for s in signals if signal_processor.validate_signal(s)]
                aggregated = signal_processor.aggregate_signals(valid_signals)
                
                logger.info("✅ signals_validated", valid=len(valid_signals), aggregated=len(aggregated))
                
                # Step 3: Analyze each token
                for signal in aggregated[:3]:  # Process top 3 signals per iteration
                    try:
                        # Get real-time market data
                        token_data = await dexscreener.get_token_data(signal.token_address)
                        
                        if not token_data:
                            logger.warning("token_data_unavailable", token=signal.token_name)
                            continue
                        
                        # AI analysis
                        analysis = await ai_agent.analyze_token(token_data)
                        
                        # Step 4: Execute trade if analysis is positive
                        if analysis['should_buy'] and analysis['confidence'] >= 0.7:
                            logger.info("🎯 buy_signal",
                                      token=token_data['name'],
                                      confidence=analysis['confidence'],
                                      reason=analysis['reason'])
                            
                            success = await trade_manager.execute_trade(token_data, analysis)
                            
                            if success:
                                logger.info("✅ trade_success", token=token_data['name'])
                            else:
                                logger.warning("⚠️ trade_failed", token=token_data['name'])
                        else:
                            logger.info("⏭️ signal_skipped",
                                      token=token_data['name'],
                                      confidence=analysis['confidence'])
                        
                        # Small delay between token analyses
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error("token_analysis_error", error=str(e), token=signal.token_name)
            
            # Step 5: Monitor existing positions
            await trade_manager.monitor_positions()
            
            # Log position summary
            summary = trade_manager.get_position_summary()
            logger.info("📊 position_summary", **summary)
            
            # Wait before next iteration (60 seconds)
            logger.info("⏸️ waiting_for_next_iteration", wait_seconds=60)
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error("❌ Error in trading loop", error=str(e), iteration=iteration)
            await asyncio.sleep(10)  # Wait before retry

async def main():
    """Main entry point"""
    setup_logger()
    logger = log.bind(module="main")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("🚀 OMNI-PROFIT SOLANA TRADING BOT")
    logger.info("=" * 60)
    logger.info("Environment", env=settings.ENV)
    logger.info("RPC", url=settings.SOLANA_RPC_URL)
    logger.info("Real Transactions", enabled=settings.ALLOW_REAL_TRANSACTIONS)
    logger.info("Max Trade Size", sol=settings.MAX_TRADE_SIZE_SOL)
    logger.info("=" * 60)
    
    # Initialize all components
    if not await initialize_components():
        logger.error("❌ Failed to initialize. Exiting.")
        sys.exit(1)
    
    logger.info("✅ Bot is now running. Press CTRL+C to stop.")
    
    # Run main trading loop
    try:
        await run_trading_loop()
    except Exception as e:
        logger.error("❌ Fatal error in main loop", error=str(e))
    finally:
        # Cleanup
        try:
            from src.analysis.dexscreener import dexscreener
            await dexscreener.close()
        except:
            pass
        logger.info("🛑 Bot stopped gracefully")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)