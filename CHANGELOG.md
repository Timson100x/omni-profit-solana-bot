# Changelog

All notable changes to this project are documented in this file.

## [Unreleased] - 2025-12-26
### Added
- `src/trading/jupiter_client.py` — Jupiter price ping helper with retries/backoff and tests.
- `scripts/devnet_e2e.py` — Devnet end-to-end smoke test (dry-run + simulation).
- `scripts/sign_only_test.py` — Build & verify a signed transaction locally (no broadcast).
- `scripts/send_devnet_transfer.py` — Controlled Devnet transfer with strong safety guards (requires `ALLOW_REAL_TRANSACTIONS=true` to actually send).
- `scripts/health_check.py` — Health check that verifies RPC and Jupiter endpoint (used by CI).
- `src/monitoring/notifier.py` — Telegram/Discord notifier (best-effort; noop without credentials).
- GitHub Actions workflow: `.github/workflows/health_check.yml` (scheduled health checks).
- `PRODUCTION_CHECKLIST.md` updated with network & testing steps.

### Changed
- Defensive compatibility patch for `httpx` / `solana` provider to handle `proxy` vs `proxies` kw. (`src/blockchain/client.py`).
- `QUICKSTART.md` updated with developer test commands and notes.

### Fixed
- Resolved AsyncClient init errors in this environment and added tests for Jupiter client.

---

## v1.0.0 - Initial Release
- Initial project scaffold and trading logic.
