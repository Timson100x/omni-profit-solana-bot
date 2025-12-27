#!/bin/bash
# 🚀 Start Bot im Codespace-kompatiblen Modus

echo "🔥 Omni Profit Solana Bot - Codespace Edition"
echo "=============================================="
echo ""
echo "📊 Mode: SIMULATION (Jupiter API in Codespace blockiert)"
echo "✅ Features:"
echo "   - Live Signal Detection (DexScreener)"
echo "   - 8-Check Validation System"
echo "   - Decision Making (AI-frei für Speed)"
echo "   - Trade Simulation"
echo "   - Position Monitoring"
echo "   - 15-second aggressive loop"
echo ""
echo "Starting bot..."
echo ""

# Kill old instances
pkill -f run_advanced_bot.py 2>/dev/null
sleep 1

# Start bot
cd /workspaces/omni-profit-solana-bot
/workspaces/omni-profit-solana-bot/.venv/bin/python run_advanced_bot.py

# Note: Für ECHTE Trades auf VPS deployen wo Jupiter API verfügbar ist!
