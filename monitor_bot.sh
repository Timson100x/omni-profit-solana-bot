#!/bin/bash
# Monitor Bot Status

echo "🤖 Omni-Profit Bot Monitor"
echo "=========================="
echo ""

# Check if bot is running
if pgrep -f "complete_system.py" > /dev/null; then
    echo "✅ Bot Status: RUNNING"
    PID=$(pgrep -f "complete_system.py")
    echo "📍 Process ID: $PID"
    echo ""
    
    # Show recent logs
    echo "📊 Recent Activity (last 10 lines):"
    echo "-----------------------------------"
    tail -10 /tmp/bot_output.log 2>/dev/null || echo "No logs found yet"
else
    echo "❌ Bot Status: STOPPED"
fi

echo ""
echo "Commands:"
echo "  Start:   /workspaces/omni-profit-solana-bot/.venv/bin/python complete_system.py &"
echo "  Stop:    pkill -f complete_system.py"
echo "  Logs:    tail -f /tmp/bot_output.log"
