import base58
from solders.keypair import Keypair
from src.core.config import settings
from src.core.logger import log

class WalletManager:
    def __init__(self):
        self.keypair = None
        self._logger = log.bind(module="wallet")

    def load_wallet(self):
        secret_key = base58.b58decode(settings.WALLET_PRIVATE_KEY)
        self.keypair = Keypair.from_bytes(secret_key)
        self._logger.info("Wallet loaded")
        return True

    def get_keypair(self):
        if not self.keypair:
            self.load_wallet()
        return self.keypair

    def get_public_key(self):
        if not self.keypair:
            self.load_wallet()
        return str(self.keypair.pubkey())

wallet_manager = WalletManager()


def get_wallet(private_key: str = None) -> Keypair:
    """Get wallet keypair from private key or settings.
    
    Args:
        private_key: Optional base58 encoded private key
    
    Returns:
        Keypair instance
    """
    if private_key is None:
        private_key = settings.WALLET_PRIVATE_KEY
    
    if not private_key:
        raise ValueError("No wallet private key provided")
    
    secret_key = base58.b58decode(private_key)
    return Keypair.from_bytes(secret_key)
