#!/bin/bash

# Ordnerstruktur erstellen
mkdir -p src/{core,blockchain,trading,signals,ai,security,web,telegram,monitoring,analysis,social}
mkdir -p docker deployment/{systemd,scripts} tests logs data config

# Init Files
touch src/__init__.py
touch src/core/__init__.py
touch src/blockchain/__init__.py
touch src/trading/__init__.py
touch src/signals/__init__.py
touch src/ai/__init__.py
touch src/security/__init__.py
touch src/web/__init__.py
touch src/telegram/__init__.py
touch src/monitoring/__init__.py
touch src/analysis/__init__.py
touch src/social/__init__.py
touch tests/__init__.py

echo "✅ Projektstruktur erstellt!"
