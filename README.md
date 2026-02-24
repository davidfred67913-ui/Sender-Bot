# Telegram Message Sender Bot (UserBot)

A Telegram bot that sends messages to any username by resolving them to chat IDs using the MTProto API.

## ⚠️ Important Difference

This bot uses **MTProto API (Telethon)** with a **real Telegram account** (phone number), NOT a bot token. This allows it to:
- ✅ Resolve usernames to chat IDs
- ✅ Send messages to users who haven't started the bot
- ✅ Access Telegram's full user database

## Features

- 📨 Send messages to any Telegram user by username
- 🔍 Automatically converts usernames to chat IDs
- ⏱️ 10-second delay between messages (configurable)
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
   - **URL**: (optional)
   - **Platform**: `Desktop`
   - **Description**: `Bot for sending messages`
5. Copy your **api_id** and **api_hash**

### 2. Local Development

```bash
cd telegram-bot

# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate
# Or Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# TELEGRAM_API_ID=12345678
# TELEGRAM_API_HASH=your_api_hash_here
# TELEGRAM_PHONE_NUMBER=+1234567890

# Run the bot
python bot.py
```

**First run only:** You'll receive a login code on Telegram. Enter it when prompted.

### 3. Deploy on Render

#### Using render.yaml

1. Push this code to GitHub/GitLab
2. Log in to [Render](https://render.com)
3. Click **"New +" → "Blueprint"**
4. Connect your repository
5. Add environment variables in Render dashboard:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_PHONE_NUMBER`
6. Deploy!

**Note:** On first deploy, check Render logs for the login code request. You may need to:
1. Use Render Shell to run the bot interactively once
2. Enter the verification code from Telegram
3. The session will be saved for future runs

#### Manual Setup

1. Log in to [Render](https://render.com)
2. Click **"New +" → "Background Worker"**
3. Connect your repository
4. Configure:
   - **Name**: `telegram-message-bot`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Add Environment Variables:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_PHONE_NUMBER`
6. Deploy

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_API_ID` | Yes | Your Telegram API ID (from my.telegram.org) |
| `TELEGRAM_API_HASH` | Yes | Your Telegram API hash (from my.telegram.org) |
| `TELEGRAM_PHONE_NUMBER` | Yes | Phone number with country code (e.g., `+1234567890`) |
| `SESSION_NAME` | No | Session file name (default: `userbot_session`) |

## Username Format

When sending messages, you can use:

- **Comma-separated**: `@user1, @user2, @user3`
- **One per line**:
  ```
  @user1
  @user2
  @user3
  ```
- With or without `@`: `user1, @user2`

## Configuration

Edit these constants in `bot.py`:

```python
MAX_USERNAMES = 50      # Maximum users per batch
DELAY_SECONDS = 10      # Delay between messages
```

## Error Messages Explained

| Error | Meaning |
|-------|---------|
| "Username not found" | The username doesn't exist |
| "User has privacy settings" | User blocked strangers from messaging |
| "Rate limited" | Too many requests, wait specified seconds |
| "Invalid user ID" | User may have deleted their account |

## Troubleshooting

### "Please enter your phone" on Render
- The session file wasn't persisted
- Use Render Shell to authenticate once interactively
- Or use a persistent disk add-on

### "API_ID_INVALID" error
- Check your API_ID and API_HASH are correct
- Get them from https://my.telegram.org/apps

### Messages not sending
- User may have privacy settings enabled
- User may have blocked your account
- Username might be incorrect

### Rate limiting (FloodWait)
- Increase `DELAY_SECONDS` in bot.py
- Telegram limits messages per minute

## File Structure

```
telegram-bot/
├── bot.py                      # Main bot code
├── requirements.txt            # Dependencies
├── render.yaml                 # Render config
├── .env.example                # Env template
├── .gitignore                  # Git ignore
├── README.md                   # This file
└── userbot_session.session     # Login session (created automatically)
```

## Security Notes

- **Never commit your `.env` file or session file**
- Your API credentials grant full account access
- Keep `TELEGRAM_API_HASH` secret
- The session file contains your login - protect it

## Limitations

- Users with strict privacy settings may not receive messages
- Telegram may rate-limit excessive messaging
- Requires a real phone number (not a virtual one)
- Some countries may have Telegram restrictions

## License

MIT License
