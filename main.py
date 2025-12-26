import asyncio
import sys
from src.core.logger import setup_logger, log
from src.core.config import settings

async def main():
    setup_logger()
    logger = log.bind(module="system")
    
    logger.info("🚀 Omni-Profit Bot - System Test")
    logger.info("ENV", env=settings.ENV)
    
    # Test 1: Config laden
    try:
        logger.info("✅ Config loaded", app=settings.APP_NAME)
    except Exception as e:
        logger.error("❌ Config failed", error=str(e))
        return
    
    # Test 2: Blockchain Client
    try:
        from src.blockchain.client import solana_client
        await solana_client.connect()
        logger.info("✅ Blockchain client ready")
    except Exception as e:
        logger.error("⚠️ Blockchain test failed (normal ohne .env)", error=str(e))
    
    # Test 3: Wallet (nur wenn Key vorhanden)
    try:
        from src.blockchain.wallet import wallet_manager
        wallet_manager.load_wallet()
        logger.info("✅ Wallet loaded", pubkey=wallet_manager.get_public_key())
    except Exception as e:
        logger.warning("⚠️ Wallet not loaded (needs WALLET_PRIVATE_KEY in .env)")
    
    logger.info("✅ System Test Complete!")
    logger.info("🚨 Add .env.production with your keys to go live")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Stopped by user")
