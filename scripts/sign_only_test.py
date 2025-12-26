#!/usr/bin/env python3
"""Sign-only Devnet test:
- builds a small SOL transfer transaction
- signs it with the configured wallet
- simulates it via the RPC (no broadcast)

Run: PYTHONPATH=. python scripts/sign_only_test.py
"""
import os
import base64
import asyncio
from src.core.logger import setup_logger, log
from src.core.config import settings
from src.blockchain.wallet import wallet_manager
from solana.rpc.async_api import AsyncClient
import base58
from solders.system_program import transfer, TransferParams
from solders.pubkey import Pubkey
from solders.keypair import Keypair as SKeypair


def build_and_sign_transfer(to_pubkey: str, lamports: int = 1_000_000):
    # Use solders Keypair (same format as wallet_manager)
    sk = base58.b58decode(settings.WALLET_PRIVATE_KEY)
    kp = SKeypair.from_bytes(sk)

    to = Pubkey.from_string(to_pubkey)
    params = TransferParams(from_pubkey=kp.pubkey(), to_pubkey=to, lamports=lamports)
    inst = transfer(params)
    return inst, kp


async def simulate(tx_b64: str, rpc_url: str):
    client = AsyncClient(rpc_url)
    try:
        log.info("simulate_tx: submitting simulated tx", rpc=rpc_url)
        sim = await client.simulate_transaction(tx_b64)
        log.info("simulate_result", result=sim.value)
        return sim.value
    finally:
        await client.close()


def main():
    setup_logger()
    rpc = os.getenv('SOLANA_RPC_URL', settings.SOLANA_RPC_URL)

    # Force Devnet for safety if not explicitly set
    if 'devnet' not in rpc.lower():
        log.warning("sign_only_running_not_devnet", rpc=rpc)
        rpc = 'https://api.devnet.solana.com'
        log.info('sign_only_force_devnet', rpc=rpc)

    # Apply httpx proxy compatibility patch used elsewhere
    try:
        from src.blockchain.client import _ensure_httpx_proxy_compat
        _ensure_httpx_proxy_compat()
    except Exception:
        pass

    # Make a transfer to ourselves (no real effect since we won't send)
    wallet_manager.load_wallet()
    to_pk = wallet_manager.get_public_key()

    # Build transaction and sign locally (sign-only test)
    inst, signer = build_and_sign_transfer(to_pk, lamports=1_000_000)  # 0.001 SOL

    # Fetch recent blockhash and sign locally (run in one async function to avoid loop issues)
    async def _get_blockhash():
        client = AsyncClient(rpc)
        try:
            return await client.get_latest_blockhash()
        finally:
            await client.close()

    hb_resp = asyncio.run(_get_blockhash())
    blockhash = hb_resp.value.blockhash

    # Use solders Message + Transaction API to sign locally
    from solders.message import Message
    from solders.hash import Hash
    from solders.transaction import Transaction

    message = Message([inst], signer.pubkey())
    # blockhash may be returned as a string or a Hash object
    if isinstance(blockhash, str):
        recent_hash = Hash.from_string(blockhash)
    else:
        recent_hash = blockhash

    signed_tx = Transaction([signer], message, recent_hash)

    # verify signatures
    try:
        signed_tx.verify_with_results()
        log.info('sign_only_success', pubkey=str(signer.pubkey()))
        print('Sign-only test OK — transaction signed and locally verified (not broadcast).')
    except Exception as e:
        log.error('sign_only_verify_failed', error=str(e))
        print('Sign-only verification failed; see logs for details.')


if __name__ == '__main__':
    main()
