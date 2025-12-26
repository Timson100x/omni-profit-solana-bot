#!/usr/bin/env bash
set -euo pipefail

ARCHIVE="/workspaces/omni-profit-changes-2025-12-26.tar.gz"
if [ ! -f "$ARCHIVE" ]; then
  echo "Archiv nicht gefunden: $ARCHIVE"
  exit 1
fi

echo "Sichere vorhandene Dateien (wenn vorhanden) mit .bak suffix..."
# Extract file list from archive and backup if they exist
for f in $(tar -tzf "$ARCHIVE"); do
  if [ -f "$f" ]; then
    echo "Backup $f -> $f.bak"
    cp -n "$f" "$f.bak" || true
  fi
done

echo "Entpacke Archiv..."
tar -xzf "$ARCHIVE"

echo "Erledigt. Prüfe die Änderungen, dann committe lokal:
  git checkout -b feat/devnet-tests-health
  git add -A
  git commit -m 'feat: add Devnet tests, health checks, notifier, controlled transfer and CI workflow'

Oder wende die Patch-Dateien manuell an, wenn du lieber ein diff benutzt.
"