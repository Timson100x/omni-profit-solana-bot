# Production Checklist — Omni-Profit Solana Bot

Kurz: sichere Schritte vor dem Start auf Mainnet.

- 1) Backup: `cp .env .env.backup.TIMESTAMP` (automatisch von `scripts/prepare_production.sh`).
- 2) Verifiziere: `WALLET_PRIVATE_KEY` in `.env` (korrektes Wallet, funds vorhanden).
- 3) Test: Führe vollständigen Devnet-Lauf und Analyse durch.
- 4) Sign-only Test: `python scripts/sign_only_test.py` (erstellt & verifiziert signaturen lokal, kein Broadcast).
- 5) Controlled Transfer: Verwende `scripts/send_devnet_transfer.py` um einen kleinen Devnet‑Transfer auszuführen. **Setze** `ALLOW_REAL_TRANSACTIONS=true` in der Umgebung, sonst wird die Transaktion nur simuliert.
- 6) Netzwerk: Stelle sicher, dass **Outbound DNS & HTTP** von der Host‑Umgebung erreichbar sind (z. B. `quote-api.jup.ag`) und dass keine Firewall/DNS‑Einschränkung besteht.
- 7) Vorbereitung: `./scripts/prepare_production.sh` (kopiert `.env.mainnet` → `.env`, installiert deps).
- 8) Starten: `./start_production.sh` (schreibt `logs/bot.log`).
- 9) Monitoring: `tail -f logs/bot.log` und aktiviere Alerts/Stop-Mechanismus.


Sicherheitshinweis: Trades auf Mainnet sind endgültig — teste zuerst auf Devnet. Stelle sicher, dass du Backups und Zugang zu Schlüsseln hast.
