#!/usr/bin/env python3
"""Devnet E2E smoke test + short simulation (dry-run).

This script:
 - Verifies Solana RPC connectivity and wallet balance
 - Pings Jupiter public price API (read-only)
 - Runs a short UltraCompoundBot simulation (N iterations)
 - Emits structured logs (uses repo logger)

Run: PYTHONPATH=. python scripts/devnet_e2e.py > logs/devnet_e2e.log
"""

import asyncio
import requests
import time

from src.core.logger import setup_logger, log
from src.core.config import settings
from src.blockchain.client import solana_client
from src.blockchain.wallet import wallet_manager
from ultra_compound_bot import UltraCompoundBot


async def rpc_checks():
    try:
        await solana_client.connect()
    except Exception as e:
        log.error("rpc_connect_failed", error=str(e))
        return

    try:
        wallet_manager.load_wallet()
        pubkey = wallet_manager.get_public_key()
    except Exception as e:
        log.error("wallet_load_failed", error=str(e))
        pubkey = None

    if pubkey:
        bal = await solana_client.get_balance(pubkey)
        log.info("wallet_balance", pubkey=pubkey, balance=bal)

    # Ping Jupiter public price endpoint (read-only) using robust helper (retries + backoff)
    try:
        from src.trading.jupiter_client import ping_jupiter
        ok = ping_jupiter()
        if ok:
            log.info("jupiter_price_ping", status="ok")
        else:
            log.warning("jupiter_ping_failed", status="unreachable")
    except Exception as e:
        log.warning("jupiter_ping_failed", error=str(e))


def run_simulation(iterations: int = 3):
    bot = UltraCompoundBot()
    log.info("simulation_start", iterations=iterations)
    for i in range(iterations):
        token = bot.find_token()
        log.info("found_token", token=token)

        should_buy = bot.analyze(token)
        if should_buy:
            log.info("signal_buy", token=token['name'])
            bot.execute_trade(token)
        else:
            log.info("signal_skip", token=token['name'])

        # short pause to make logs readable
        time.sleep(1)

    log.info("simulation_end", final_balance=bot.balance, trades=bot.trades, wins=bot.wins, total_profit=bot.total_profit)


async def main():
    setup_logger()
    log.info("devnet_e2e_start", env=settings.ENV, rpc=settings.SOLANA_RPC_URL)

    if 'devnet' not in settings.SOLANA_RPC_URL.lower():
        log.warning("not_on_devnet", rpc=settings.SOLANA_RPC_URL)

    await rpc_checks()

    # Run a short simulated trading loop
    run_simulation(iterations=3)

    log.info("devnet_e2e_complete")


if __name__ == '__main__':
    asyncio.run(main())
