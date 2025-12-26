import asyncio
from src.core.logger import setup_logger, log
from src.blockchain.client import solana_client
from src.trading.manager import trade_manager

async def main():
    setup_logger()
    logger = log.bind(module="system")
    logger.info("🚀 Omni-Profit Bot wird gestartet...")
    
    await solana_client.connect()
    logger.info("✅ Alle Systeme online")
    
    await trade_manager.monitor_positions()

if __name__ == "__main__":
    asyncio.run(main())
