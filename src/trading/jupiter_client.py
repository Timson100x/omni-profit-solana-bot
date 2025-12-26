"""Simple Jupiter API helper with retries and health check.

Provides:
 - ping_jupiter() -> bool
 - get_jupiter_price_stub() -> dict | None

This is intentionally small and conservative: we only do read-only requests
and never rely on Jupiter for critical decisions without fallback.
"""

import os
import time
from typing import Optional

import requests
from src.core.logger import log

JUPITER_URL = os.getenv("JUPITER_PRICE_URL", "https://quote-api.jup.ag/v1/price")
JUPITER_TIMEOUT = float(os.getenv("JUPITER_TIMEOUT", "5"))
JUPITER_RETRIES = int(os.getenv("JUPITER_RETRIES", "3"))
JUPITER_BACKOFF = float(os.getenv("JUPITER_BACKOFF", "0.5"))


def _request_with_retries(url: str, timeout: float, retries: int, backoff: float) -> Optional[requests.Response]:
    attempt = 0
    while attempt < retries:
        try:
            log.info("jupiter_request_attempt", url=url, attempt=attempt + 1)
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            attempt += 1
            log.warning("jupiter_request_failed", url=url, attempt=attempt, error=str(e))
            if attempt < retries:
                sleep_for = backoff * (2 ** (attempt - 1))
                time.sleep(sleep_for)
    return None


def ping_jupiter() -> bool:
    """Ping Jupiter price API, with retries. Returns True if reachable."""
    r = _request_with_retries(JUPITER_URL, JUPITER_TIMEOUT, JUPITER_RETRIES, JUPITER_BACKOFF)
    if r is None:
        log.error("jupiter_unreachable", url=JUPITER_URL)
        return False
    log.info("jupiter_reachable", url=JUPITER_URL, status=r.status_code)
    return True


def get_jupiter_price_stub() -> Optional[dict]:
    """Attempt to fetch a price; returns parsed JSON or None on failure."""
    r = _request_with_retries(JUPITER_URL, JUPITER_TIMEOUT, JUPITER_RETRIES, JUPITER_BACKOFF)
    if not r:
        return None
    try:
        return r.json()
    except Exception:
        log.warning("jupiter_invalid_json", url=JUPITER_URL)
        return None
