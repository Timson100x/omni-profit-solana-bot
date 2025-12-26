Release & PR instructions

These are the recommended commands to create a branch, commit the changes and open a PR on GitHub from your local environment:

# Create branch & commit

git checkout -b feat/devnet-tests-health
git add -A
git commit -m "feat: add Devnet testing, health checks, notifier, controlled transfer and CI workflow"

# Push & open PR

git push --set-upstream origin feat/devnet-tests-health
# Then open a PR, or use GitHub CLI:
# gh pr create --title "Devnet: tests & health checks" --body-file .github/PULL_REQUEST_TEMPLATE.md --base main

Notes:
- The PR template is stored in `.github/PULL_REQUEST_TEMPLATE.md`. Review before creating the PR.
- Add notifier credentials to `.env.production` (Telegram/Discord) to enable alert delivery:
  - TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  - DISCORD_WEBHOOK_URL

If you want, I can prepare a patch file (unified diff) you can apply locally; tell me and I’ll generate it."}EOF