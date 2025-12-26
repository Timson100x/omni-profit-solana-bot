#!/bin/bash
echo "Erstelle main.py..."
cat > main.py << 'EOFMAIN'
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
EOFMAIN

echo "Erstelle .env.production template..."
cat > .env.production.example << 'EOFENV'
WALLET_PRIVATE_KEY=<YOUR_BASE58_KEY>
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
TELEGRAM_API_ID=<YOUR_ID>
TELEGRAM_API_HASH=<YOUR_HASH>
TELEGRAM_PHONE=+49123456789
TELEGRAM_CHANNEL_ID=<CHANNEL_ID>
GEMINI_API_KEY=<YOUR_KEY>
EOFENV

echo "✅ Alle Dateien erstellt!"
