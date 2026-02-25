# Telegram Message Sender Bot (UserBot)

A Telegram bot that sends messages to any username by resolving them to chat IDs using the MTProto API.

## ⚠️ Important: Render Deployment Issue Fix

If your bot shows "Live" on Render but doesn't respond to Telegram messages, **you need to authenticate first**. This is a one-time setup.

## Quick Fix (Most Common Issue)

### Step 1: Generate SESSION_STRING Locally

Run this on your computer (not Render):

```bash
# Install dependencies
pip install telethon

# Run the session generator
python generate_session.py
```

Enter your credentials when prompted. You'll get a long string like:
```
1BQANOTEzAAAAT... (very long string)
```

### Step 2: Add to Render Environment Variables

1. Go to your Render dashboard → Your Service → Environment
2. Add these variables:
   - `TELEGRAM_API_ID` = your_api_id
   - `TELEGRAM_API_HASH` = your_api_hash
   - `TELEGRAM_PHONE_NUMBER` = +1234567890
   - `SESSION_STRING` = (the long string from step 1)
3. Click "Save Changes"
4. Your bot will restart and work!

---

## Features

- 📨 Send messages to any Telegram user by username
- 🔍 Automatically converts usernames to chat IDs
- ⏱️ 10-second delay between messages
- 📊 Progress updates and completion summary
- 🛡️ Error handling for invalid/deleted users
- 👥 Up to 50 usernames per batch

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/send` | Begin sending messages |
| `/help` | Show help information |

## How to Use

1. Send `/send` to the bot
2. Type your message
3. Enter usernames (e.g., `@user1, @user2, @user3`)
4. Bot resolves each username to chat ID and sends messages
5. Receive completion summary

## Setup Instructions

### 1. Get Telegram API Credentials

1. Go to [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your phone number
3. Click **"API development tools"**
4. Create a new application:
   - **App title**: `Message Sender Bot`
   - **Short name**: `msgbot`
   - **Platform**: `Desktop`
   - **Description**: `Bot for sending messages`
5. Copy your **api_id** and **api_hash**

### 2. Local Development

```bash
cd telegram-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run locally (will ask for verification code on first run)
python bot.py
```

### 3. Deploy on Render (Correct Way)

#### Option A: Using SESSION_STRING (Recommended)

1. **Generate SESSION_STRING locally:**
   ```bash
   python generate_session.py
   ```

2. **Copy the output** (long string)

3. **Add to Render Environment Variables:**
   - `TELEGRAM_API_ID` = your_api_id
   - `TELEGRAM_API_HASH` = your_api_hash  
   - `TELEGRAM_PHONE_NUMBER` = +1234567890
   - `SESSION_STRING` = (paste the long string)

4. **Deploy!** The bot will start immediately without needing interactive input.

#### Option B: Using Render Shell (Alternative)

If you didn't generate SESSION_STRING:

1. Deploy the bot to Render (it will fail to authenticate)
2. Go to Render Dashboard → Your Service → Shell
3. Run: `python bot.py`
4. Check logs for "Authentication code sent to your Telegram"
5. Enter the code when prompted in the shell
6. Once authenticated, the session file is created
7. **Note:** On free tier, this may not persist after restart!

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_API_ID` | Yes | Your Telegram API ID |
| `TELEGRAM_API_HASH` | Yes | Your Telegram API hash |
| `TELEGRAM_PHONE_NUMBER` | Yes | Phone with country code (e.g., `+1234567890`) |
| `SESSION_STRING` | **Recommended** | Generated session string for Render |
| `TELEGRAM_2FA_PASSWORD` | If 2FA enabled | Your 2FA password |

## Troubleshooting

### Bot shows "Live" but doesn't respond

**Cause:** Not authenticated

**Fix:**
1. Run `python generate_session.py` locally
2. Add the SESSION_STRING to Render env vars
3. Redeploy

### "SESSION_STRING is invalid" error

**Cause:** Wrong session string or credentials changed

**Fix:** Regenerate SESSION_STRING with `python generate_session.py`

### "API_ID_INVALID" error

**Cause:** Wrong API credentials

**Fix:** Double-check your API_ID and API_HASH from my.telegram.org

### "FloodWait" error

**Cause:** Too many messages sent too quickly

**Fix:** Increase `DELAY_SECONDS` in bot.py (default is 10)

### Messages fail to send to some users

**Cause:** User privacy settings

**Fix:** Nothing - some users block messages from non-contacts

## Username Format

- **Comma-separated**: `@user1, @user2, @user3`
- **One per line**:
  ```
  @user1
  @user2
  @user3
  ```
- With or without `@`: `user1, @user2`

## Configuration

Edit in `bot.py`:
```python
MAX_USERNAMES = 50      # Maximum users per batch
DELAY_SECONDS = 10      # Delay between messages
```

## File Structure

```
telegram-bot/
├── bot.py                 # Main bot code
├── generate_session.py    # Helper to create SESSION_STRING
├── requirements.txt       # Dependencies
├── render.yaml            # Render config
├── .env.example           # Env template
├── .gitignore             # Git ignore
└── README.md              # This file
```

## Security Notes

- **Never commit SESSION_STRING or .env files**
- SESSION_STRING grants full account access - keep it secret
- Use environment variables, never hardcode credentials

## License

MIT License
