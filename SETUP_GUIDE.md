# 🔧 Complete Setup Guide - Omni-Profit Solana Bot

## ✅ Already Done!

- ✅ Codespace running
- ✅ .env configured (Devnet)
- ✅ WALLET_PRIVATE_KEY set
- ✅ SOLANA_RPC_URL (Devnet)
- ✅ GEMINI_API_KEY set
- ✅ Dependencies ready

---

## 📝 Missing: API Keys for Signal Sources

### 1️⃣ Telegram API (Required for Telegram signals)

**Get your keys:**
1. Go to: https://my.telegram.org/auth
2. Enter your phone number (international format: +491234567890)
3. Enter the verification code from Telegram
4. Click "API development tools"
5. Create a new application
6. Copy:
   - **api_id** (number)
   - **api_hash** (long string)
   - **phone** (your number with +)
   - **channel_id** (Telegram channel you want to monitor)

**Example:**
```
api_id: 12345678
api_hash: abc123def456ghi789jkl012mno345pq
phone: +491234567890
channel_id: @your_channel or -1001234567890
```

---

### 2️⃣ Discord Bot Token (Optional for Discord signals)

**Create a Bot:**
1. Go to: https://discord.com/developers/applications
2. Login to Discord
3. Click "New Application" → Name it (e.g., "Solana Bot")
4. Go to "Bot" tab → "Add Bot"
5. Click "Reset Token" → Copy the token
6. Enable "Message Content Intent" under "Privileged Gateway Intents"
7. Save changes

**Example Token (placeholder):**
```
REPLACE_WITH_YOUR_DISCORD_BOT_TOKEN
```

**Invite Bot to Server:**
- Go to "OAuth2" → "URL Generator"
- Select: `bot`, `messages.read`, `channels.read`
- Copy URL and open in browser

---

### 3️⃣ X/Twitter Bearer Token (Optional for Twitter signals)

**⚠️ Your account needs verification first!**

1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Click "Settings" and verify:
   - Phone number
   - Email address
3. Create a new Project + App
4. Go to App Settings → "Keys and tokens"
5. Generate "Bearer Token"
6. Copy the token

**Example Token:**
```
AAAAAAAAAAAAAAAAAAAAAPqRswEAAAAA1234567890AbCdEfGhIjKlMnOpQrStUvWxYz
```

---

## 🚀 Easy Setup with Script

**Run this command and paste your keys:**
```bash
./setup_keys.sh
```

The script will ask for:
1. Telegram API_ID, API_HASH, PHONE, CHANNEL_ID
2. Discord BOT_TOKEN
3. X BEARER_TOKEN

All keys will be automatically added to `.env`!

---

## 🔨 Manual Setup (Alternative)

Edit `.env` directly:
```bash
nano .env
```

Fill in:
```bash
# Telegram
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+491234567890
TELEGRAM_CHANNEL_ID=@yourchannel

# Discord (optional)
DISCORD_BOT_TOKEN=your_discord_token_here

# X/Twitter (optional)
X_BEARER_TOKEN=your_bearer_token_here
```

Save: `Ctrl+O`, Exit: `Ctrl+X`

---

## 🎯 Start the Bot

```bash
./start.sh
```

---

## 💡 Tips

- Start with **Telegram only** - it's the easiest
- Discord & Twitter are **optional** (nice-to-have)
- Test on **Devnet first** before switching to Mainnet
- Your 6 SOL in Phantom are **Testnet SOL** (no real value)

---

## 🔄 Switch to Mainnet (CAREFUL!)

```bash
sed -i 's|devnet|mainnet-beta|g' .env
```

⚠️ **Only do this when:**
- Bot runs stable on Devnet
- You understand the risks
- You use a separate wallet with small amounts

---

## ❓ Problems?

**Telegram Error:**
- Double-check API_ID and API_HASH
- Make sure phone has + and country code
- Try logging into Telegram web first

**Discord Error:**
- Bot token must be valid
- Bot must be invited to your server
- Message Content Intent must be enabled

**X/Twitter Error:**
- Account must be verified (phone + email)
- Bearer Token expires - regenerate if needed

