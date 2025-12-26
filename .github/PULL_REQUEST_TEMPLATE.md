## Summary

This PR bundles the Devnet testing & safety improvements:

- Jupiter retries + tests
- Devnet E2E smoke test and sign-only tests
- Controlled Devnet transfer script (safe by default)
- Health check + GitHub Actions scheduled workflow
- Notifier (Telegram/Discord) hooks for critical alerts
- Compatibility patch for httpx/solana proxy signature

## Testing
- Run `PYTHONPATH=. python scripts/devnet_e2e.py` (dry-run + simulation)
- Run `PYTHONPATH=. python scripts/sign_only_test.py` (sign-only)
- Run `PYTHONPATH=. python scripts/send_devnet_transfer.py` with `ALLOW_REAL_TRANSACTIONS=true` to perform a small controlled transfer
- The health check runs on CI every 30 minutes (workflow included).

## Notes
- All changes are non-breaking and add safety nets and monitoring for production readiness.
- Please review the CHECKLIST and QUICKSTART updates.
