"""Notifier helpers (Telegram / Discord / noop).

Sends notifications if credentials are present; otherwise logs a no-op.
Usage is conservative: only send alerts when critical (health check fails or tx events).
"""
import os
import requests
from typing import Optional
from src.core.logger import log

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.info("telegram_noop", reason="missing_credentials")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=5)
        r.raise_for_status()
        log.info("telegram_sent", text=text)
        return True
    except Exception as e:
        log.warning("telegram_failed", error=str(e))
        return False


def send_discord(text: str) -> bool:
    if not DISCORD_WEBHOOK:
        log.info("discord_noop", reason="missing_webhook")
        return False
    try:
        r = requests.post(DISCORD_WEBHOOK, json={"content": text}, timeout=5)
        r.raise_for_status()
        log.info("discord_sent", text=text)
        return True
    except Exception as e:
        log.warning("discord_failed", error=str(e))
        return False


def notify_critical(text: str) -> None:
    """Send to all available channels (best-effort)."""
    log.error("notify_critical", text=text)
    send_telegram(text)
    send_discord(text)