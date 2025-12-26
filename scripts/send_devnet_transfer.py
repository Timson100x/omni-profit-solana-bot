#!/usr/bin/env python3
"""Controlled Devnet transfer (small amount) with safety guards.

Behavior:
 - By default does not broadcast (safe). Set ALLOW_REAL_TRANSACTIONS=true in env to enable.
 - Sends a small transfer (DEFAULT_LAMPORTS) from configured wallet to a target.
 - Notifies via notifier on success/failure (best-effort).
"""
import os
import asyncio
import base58
from decimal import Decimal
from src.core.logger import setup_logger, log
from src.core.config import settings
from src.blockchain.wallet import wallet_manager
from solders.system_program import transfer, TransferParams
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.message import Message
from solders.transaction import Transaction
from solana.rpc.async_api import AsyncClient
from src.monitoring.notifier import notify_critical

DEFAULT_LAMPORTS = int(0.01 * 1_000_000_000)  # 0.01 SOL

def _send_transfer(to_pubkey: str, lamports: int = DEFAULT_LAMPORTS) -> dict:
    rpc = os.getenv('SOLANA_RPC_URL', settings.SOLANA_RPC_URL)
    if 'devnet' not in rpc.lower():
        log.warning('send_devnet_transfer_not_on_devnet', rpc=rpc)
        # Force devnet for safety
        rpc = 'https://api.devnet.solana.com'

    ALLOW = os.getenv('ALLOW_REAL_TRANSACTIONS', 'false').lower() == 'true'
    if not ALLOW:
        log.warning('send_devnet_transfer_blocked', reason='ALLOW_REAL_TRANSACTIONS not true')

    wallet_manager.load_wallet()
    from_pk = Pubkey.from_string(wallet_manager.get_public_key())
    to_pk = Pubkey.from_string(to_pubkey)

    kp = Keypair.from_bytes(base58.b58decode(settings.WALLET_PRIVATE_KEY))

    params = TransferParams(from_pubkey=from_pk, to_pubkey=to_pk, lamports=lamports)
    inst = transfer(params)

    async def _do():
        # Ensure httpx/solana provider compatibility
        try:
            from src.blockchain.client import _ensure_httpx_proxy_compat
            _ensure_httpx_proxy_compat()
        except Exception:
            pass

        client = AsyncClient(rpc)
        try:
            hb = await client.get_latest_blockhash()
            msg = Message([inst], kp.pubkey())
            recent_hash = hb.value.blockhash
            tx = Transaction([kp], msg, recent_hash)
            # Simulate first
            sim = await client.simulate_transaction(tx)
            if getattr(sim, 'err', None):
                log.error('devnet_transfer_simulation_failed', err=sim.err)
                notify_critical(f"Devnet transfer simulation failed: {sim.err}")
                return {'ok': False, 'reason': 'simulation_failed', 'sim': sim.err}

            if not ALLOW:
                log.info('devnet_transfer_simulation_ok_not_sent')
                return {'ok': True, 'sent': False, 'sim': sim}

            # Send real
            resp = await client.send_transaction(tx)
            sig = resp.value
            log.info('devnet_transfer_sent', signature=str(sig))
            # confirm
            await client.confirm_transaction(sig)
            log.info('devnet_transfer_confirmed', signature=str(sig))
            try:
                notify_critical(f"Devnet transfer sent: {sig} (lamports={lamports})")
            except Exception:
                pass
            return {'ok': True, 'sent': True, 'signature': str(sig)}
        finally:
            await client.close()

    return asyncio.run(_do())


if __name__ == '__main__':
    setup_logger()
    # Default to sending to self (round-trip) for safety
    wallet_manager.load_wallet()
    to_pk = wallet_manager.get_public_key()
    res = _send_transfer(to_pk)
    print(res)
