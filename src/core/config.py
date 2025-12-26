import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Omni Profit Bot"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    
    SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    SOLANA_WS_URL: str = os.getenv("SOLANA_WS_URL", "wss://api.mainnet-beta.solana.com")
    COMMITMENT: str = "confirmed"
    
    WALLET_PRIVATE_KEY: str
    WALLET_ENCRYPTED: bool = False
    
    MAX_TRADE_SIZE_SOL: float = 0.1
    MIN_TRADE_SIZE_SOL: float = 0.05
    MAX_DAILY_LOSS_SOL: float = 1.0
    SLIPPAGE_TOLERANCE: float = 0.05
    TAKE_PROFIT_MULTIPLIER: float = 2.0
    STOP_LOSS_PCT: float = 0.30
    
    TELEGRAM_API_ID: str
    TELEGRAM_API_HASH: str
    TELEGRAM_PHONE: str
    TELEGRAM_CHANNEL_ID: str
    
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    CLAUDE_API_KEY: Optional[str] = None
    
    DISCORD_BOT_TOKEN: Optional[str] = None
    DISCORD_CHANNEL_IDS: Optional[str] = None
    X_BEARER_TOKEN: Optional[str] = None

    # Safety & operation
    EMERGENCY_STOP: bool = False
    ALLOW_REAL_TRANSACTIONS: bool = False
    
    REDIS_URL: str = "redis://redis:6379"

    class Config:
        env_file = ".env.production"
        extra = "ignore"

settings = Settings()
