#!/bin/bash
# Setup Perplexity MCP in GitHub Codespace

echo "══════════════════════════════════════════════════════════════════════"
echo "🔧 Perplexity MCP Setup für GitHub Codespaces"
echo "══════════════════════════════════════════════════════════════════════"
echo ""

# Check if running in Codespace
if [ -z "$CODESPACES" ]; then
    echo "⚠️  Warning: Not running in GitHub Codespace"
    echo "   This script is optimized for Codespaces but will work anyway"
    echo ""
fi

# Check Node.js
echo "1️⃣  Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "   ✅ Node.js installed: $NODE_VERSION"
else
    echo "   ❌ Node.js not found - installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
echo ""

# Check npm
echo "2️⃣  Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "   ✅ npm installed: $NPM_VERSION"
else
    echo "   ❌ npm not found"
    exit 1
fi
echo ""

# Install Perplexity MCP Server
echo "3️⃣  Installing Perplexity MCP Server..."
echo "   (This might take a minute...)"

# Test if server is accessible
npx -y @perplexity-ai/mcp-server --version 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Perplexity MCP Server installed"
else
    echo "   ℹ️  Perplexity MCP Server will be installed on first use"
fi
echo ""

# Check for API Key
echo "4️⃣  Checking API Key..."
if [ -z "$PERPLEXITY_API_KEY" ]; then
    echo "   ⚠️  PERPLEXITY_API_KEY not set"
    echo ""
    echo "   Get your API Key:"
    echo "   1. Go to: https://www.perplexity.ai/settings/api"
    echo "   2. Create API Key (requires Perplexity Pro)"
    echo "   3. Add to Codespace Secrets or .env file"
    echo ""
    
    read -p "   Enter your Perplexity API Key (or press Enter to skip): " api_key
    
    if [ -n "$api_key" ]; then
        export PERPLEXITY_API_KEY="$api_key"
        
        # Add to .env.production
        if [ -f ".env.production" ]; then
            if grep -q "PERPLEXITY_API_KEY" .env.production; then
                sed -i "s/^PERPLEXITY_API_KEY=.*/PERPLEXITY_API_KEY=$api_key/" .env.production
            else
                echo "" >> .env.production
                echo "# Perplexity MCP" >> .env.production
                echo "PERPLEXITY_API_KEY=$api_key" >> .env.production
            fi
            echo "   ✅ API Key saved to .env.production"
        fi
        
        # Add to .bashrc for persistence
        if ! grep -q "PERPLEXITY_API_KEY" ~/.bashrc; then
            echo "" >> ~/.bashrc
            echo "# Perplexity MCP" >> ~/.bashrc
            echo "export PERPLEXITY_API_KEY=$api_key" >> ~/.bashrc
            echo "   ✅ API Key added to ~/.bashrc"
        fi
    else
        echo "   ⏭️  Skipped - Add API Key later"
    fi
else
    echo "   ✅ PERPLEXITY_API_KEY found"
fi
echo ""

# GitHub Token check
echo "5️⃣  Checking GitHub Token..."
if [ -n "$GITHUB_TOKEN" ]; then
    echo "   ✅ GITHUB_TOKEN found (for GitHub MCP integration)"
else
    echo "   ℹ️  GITHUB_TOKEN not set (optional for GitHub MCP)"
    echo "   Available in Codespace by default as \$GITHUB_TOKEN"
fi
echo ""

# Verify MCP config files
echo "6️⃣  Verifying MCP configuration..."
if [ -f ".vscode/mcp.json" ]; then
    echo "   ✅ .vscode/mcp.json exists"
else
    echo "   ❌ .vscode/mcp.json missing"
fi

if [ -f ".vscode/settings.json" ]; then
    echo "   ✅ .vscode/settings.json exists"
else
    echo "   ❌ .vscode/settings.json missing"
fi
echo ""

# Test MCP Server
echo "7️⃣  Testing Perplexity MCP Server..."
if [ -n "$PERPLEXITY_API_KEY" ]; then
    echo "   Running test query..."
    
    # Simple test (will timeout but shows if server starts)
    timeout 5s npx -y @perplexity-ai/mcp-server 2>&1 | grep -q "server" && \
        echo "   ✅ MCP Server responds" || \
        echo "   ℹ️  Server will start automatically when needed"
else
    echo "   ⏭️  Skipping test (no API key)"
fi
echo ""

# Final instructions
echo "══════════════════════════════════════════════════════════════════════"
echo "✅ Setup Complete!"
echo "══════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1️⃣  Restart VS Code window:"
echo "   → Command Palette (Ctrl+Shift+P)"
echo "   → 'Developer: Reload Window'"
echo ""
echo "2️⃣  Verify MCP in Copilot Chat:"
echo "   → Open GitHub Copilot Chat"
echo "   → Type: '@perplexity search for Solana DEX APIs'"
echo "   → Should see Perplexity results with citations"
echo ""
echo "3️⃣  Available MCP Tools:"
echo "   • ask_perplexity - Web search with citations"
echo "   • search_perplexity - Fast search"
echo "   • Models: sonar-pro, sonar, sonar-reasoning"
echo ""
echo "4️⃣  Example Queries:"
echo "   • 'Find latest Solana RPC endpoints'"
echo "   • 'Best practices for MEV protection'"
echo "   • 'Raydium pool creation events'"
echo ""
echo "🔗 Resources:"
echo "   API Keys: https://www.perplexity.ai/settings/api"
echo "   MCP Docs: https://docs.perplexity.ai/guides/mcp-server"
echo ""
echo "⚠️  Note: Perplexity Pro subscription required for API access"
echo ""
