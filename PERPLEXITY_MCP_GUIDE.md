# 🔍 Perplexity MCP Integration Guide

## Was ist MCP?

**Model Context Protocol (MCP)** ermöglicht AI-Assistenten (GitHub Copilot, Cursor, etc.) externe Tools und APIs zu nutzen. Mit Perplexity MCP bekommst du:

- ✅ **Echtzeit Web-Suche** direkt in VS Code
- ✅ **Zitierte Antworten** mit Quellen
- ✅ **Aktuelle Informationen** (nicht nur Training Data)
- ✅ **Solana/Crypto-spezifische Suchen** für Bot-Development

## 🚀 Quick Setup

### 1. Installation

```bash
# Automatisches Setup
chmod +x setup_perplexity_mcp.sh
./setup_perplexity_mcp.sh
```

### 2. API Key holen

1. Gehe zu: https://www.perplexity.ai/settings/api
2. **Perplexity Pro** Abo erforderlich ($20/Monat)
3. Create API Key
4. Kopiere Key

### 3. API Key konfigurieren

**Option A: Codespace Secrets (Empfohlen)**
```bash
# In GitHub:
# Repo → Settings → Secrets → Codespaces
# Add: PERPLEXITY_API_KEY=dein_key
```

**Option B: .env.production**
```bash
echo "PERPLEXITY_API_KEY=dein_key" >> .env.production
```

**Option C: Terminal**
```bash
export PERPLEXITY_API_KEY=dein_key
```

### 4. VS Code neu laden

```
Ctrl+Shift+P → "Developer: Reload Window"
```

## 💡 Verwendung in VS Code

### In GitHub Copilot Chat:

```
# Web-Suche mit Perplexity
@perplexity search for latest Solana RPC endpoints

# Detaillierte Analyse
@perplexity explain MEV protection on Solana

# Trading-spezifisch
@perplexity best practices for DEX arbitrage bots

# Code-Beispiele
@perplexity show me Jupiter swap examples in Python
```

### Verfügbare Tools:

```javascript
// 1. ask_perplexity - Volle Suche mit Citations
{
  "tool": "ask_perplexity",
  "query": "How to detect rug pulls on Solana?",
  "model": "sonar-pro"
}

// 2. search_perplexity - Schnelle Suche
{
  "tool": "search_perplexity", 
  "query": "Raydium pool creation events"
}
```

### Verfügbare Modelle:

- **sonar-pro** - Beste Qualität, Citations (empfohlen)
- **sonar** - Schneller, gute Qualität
- **sonar-reasoning** - Tiefe Analyse

## 🔥 Use Cases für deinen Trading Bot

### 1. Research während Development

```
@perplexity find latest Jito bundle API documentation

@perplexity how to monitor Raydium pools via WebSocket

@perplexity best Solana RPC providers for trading bots
```

### 2. Debug-Hilfe

```
@perplexity common errors with solana-py library

@perplexity how to fix "Transaction simulation failed"

@perplexity best practices for handling Solana RPC rate limits
```

### 3. Market Intelligence

```
@perplexity current MEV protection methods on Solana

@perplexity new DEX launches on Solana December 2025

@perplexity how do professional trading bots avoid detection
```

### 4. Code-Verbesserungen

```
@perplexity optimize Python async WebSocket connections

@perplexity best way to validate Solana token contracts

@perplexity how to calculate optimal slippage for DEX swaps
```

## 🎯 Praktische Beispiele

### Beispiel 1: RPC Endpoint finden

**Chat:**
```
@perplexity find fastest free Solana RPC endpoints for trading
```

**Perplexity liefert:**
- Liste aktueller RPC Endpoints
- Performance Vergleiche
- Rate Limits
- Quellen mit Links

### Beispiel 2: Smart Contract Research

**Chat:**
```
@perplexity explain Raydium AMM pool initialization parameters
```

**Perplexity liefert:**
- Technical Details
- Code Examples
- Official Docs
- GitHub Links

### Beispiel 3: Trading Strategies

**Chat:**
```
@perplexity profitable arbitrage strategies for Solana DEXes 2025
```

**Perplexity liefert:**
- Aktuelle Strategien
- Risk Analysis
- Tool Recommendations
- Community Discussions

## ⚙️ Konfiguration

### .vscode/mcp.json

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "${env:PERPLEXITY_API_KEY}",
        "PERPLEXITY_MODEL": "sonar-pro"
      }
    }
  }
}
```

### .vscode/settings.json

```json
{
  "github.copilot.advanced": {
    "mcp.enabled": true
  },
  "mcp.servers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "${env:PERPLEXITY_API_KEY}",
        "PERPLEXITY_MODEL": "sonar-pro"
      }
    }
  }
}
```

## 🧪 Testing

### Test 1: Basic Search

```bash
# In VS Code Chat
@perplexity test search: current Solana price
```

**Expected:** Aktuelle SOL Preis mit Quellen

### Test 2: Technical Query

```bash
@perplexity how to use Jito bundles for MEV protection
```

**Expected:** Detailed answer mit Code-Beispielen

### Test 3: Real-time Data

```bash
@perplexity latest Solana DeFi exploits December 2025
```

**Expected:** Aktuelle News mit Links

## 🔧 Troubleshooting

### "MCP Server not found"

```bash
# Manuell installieren
npm install -g @perplexity-ai/mcp-server

# Oder per npx (automatisch)
npx -y @perplexity-ai/mcp-server
```

### "API Key invalid"

1. Check API Key: https://www.perplexity.ai/settings/api
2. Verify Perplexity Pro aktiv
3. Neu generieren wenn abgelaufen

```bash
# Test API Key
curl https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

### "MCP not appearing in Copilot"

1. VS Code neu laden: `Ctrl+Shift+P` → "Reload Window"
2. GitHub Copilot Extension aktualisieren
3. Check `.vscode/mcp.json` existiert
4. Check `PERPLEXITY_API_KEY` gesetzt

### Rate Limits

**Perplexity API Limits:**
- Pro: 5000 requests/month
- Standard: 500/month

**Monitor Usage:**
https://www.perplexity.ai/settings/api

## 💰 Kosten

**Perplexity Pro:**
- $20/Monat
- 5000 API Calls
- Unlimited Perplexity Web
- Priority Support

**Für Trading Bot Development:**
- ~50-100 queries/day = 1500-3000/month
- Gut innerhalb Limit
- **Lohnt sich** für bessere Code-Qualität

## 🔗 Alternative: GitHub MCP

Bonus: GitHub MCP auch konfiguriert in `mcp.json`:

```bash
@github search for Solana trading bot examples

@github find issues about Jito bundles in solana-py repo
```

## 📚 Resources

- **Perplexity API:** https://www.perplexity.ai/settings/api
- **MCP Docs:** https://docs.perplexity.ai/guides/mcp-server
- **VS Code MCP:** https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- **GitHub MCP:** https://github.com/perplexityai/modelcontextprotocol

## 🎉 Quick Start Checklist

- [ ] Run `./setup_perplexity_mcp.sh`
- [ ] Add Perplexity API Key
- [ ] Reload VS Code window
- [ ] Test: `@perplexity test search`
- [ ] Use für Bot Research!

---

**Pro Tip:** Kombiniere Perplexity mit deinem Bot:

```python
# In bot code
@perplexity find current gas prices on Solana

# Dann implementiere basierend auf research
# src/blockchain/gas_optimizer.py
```

Happy Coding! 🚀
