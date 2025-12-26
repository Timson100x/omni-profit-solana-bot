#!/usr/bin/env python3
"""Simple health check for RPC and Jupiter price endpoint.

Exits with code 0 when both checks pass, otherwise non-zero.
Prints JSON lines for easy parsing.
"""
import sys
import json
from src.core.logger import setup_logger, log
from src.core.config import settings
from src.trading.jupiter_client import ping_jupiter
from src.blockchain.client import solana_client


async def _rpc_check():
    try:
        await solana_client.connect()
        log.info("health_rpc_ok", url=settings.SOLANA_RPC_URL)
        return True
    except Exception as e:
        log.error("health_rpc_failed", error=str(e))
        return False


def main():
    setup_logger()
    # Ping Jupiter
    j = ping_jupiter()

    # RPC check (sync run of async)
    import asyncio
    r = asyncio.run(_rpc_check())

    ok = j and r
    log.info("health_check_result", ok=ok, jupiter=j, rpc=r)

    if not ok:
        try:
            from src.monitoring.notifier import notify_critical
            notify_critical(f"Health check failed: jupiter={j}, rpc={r}")
        except Exception:
            pass

    sys.exit(0 if ok else 2)


if __name__ == '__main__':
    main()
