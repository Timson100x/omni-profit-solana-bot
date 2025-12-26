Title: feat: Devnet tests, health checks, notifier, controlled transfer

Body:

This PR adds safety and testing improvements to prepare the project for Mainnet readiness:

- Add Jupiter helper with retries/backoff and tests (`src/trading/jupiter_client.py`) ✅
- Devnet E2E smoke test (dry-run + simulation) (`scripts/devnet_e2e.py`) ✅
- Sign-only transaction verification (`scripts/sign_only_test.py`) — build & verify signatures locally (no broadcast) ✅
- Controlled Devnet transfer tool (`scripts/send_devnet_transfer.py`) — **disabled by default**; requires `ALLOW_REAL_TRANSACTIONS=true` to actually send ✅
- Health check (`scripts/health_check.py`) + GitHub Actions workflow `.github/workflows/health_check.yml` (scheduled) ✅
- Notifier hooks (`src/monitoring/notifier.py`) for critical alerts (Telegram/Discord) ✅
- Small compatibility patch: `httpx`/`solana` proxy compatibility to avoid runtime TypeErrors ✅

Testing steps:
- `PYTHONPATH=. python scripts/devnet_e2e.py` (dry-run + simulation)
- `PYTHONPATH=. python scripts/sign_only_test.py` (sign-only)
- `ALLOW_REAL_TRANSACTIONS=true PYTHONPATH=. python scripts/send_devnet_transfer.py` (small Devnet transfer)
- `PYTHONPATH=. python scripts/health_check.py` (health check)

Notes:
- `PRODUCTION_CHECKLIST.md` updated with network requirements and test steps.
- Please set notifier credentials in `.env.production` to enable Telegram/Discord alerts.

If you'd like, I can also open the PR using the GitHub CLI (requires repo push access from your environment).