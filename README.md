# Telegram Message Sender Bot

A Telegram bot that sends messages to multiple users with a delay between each message. Designed to run as a Render Background Worker.

## Features

- 📨 Send messages to up to 50 Telegram users at once
- ⏱️ 10-second delay between each message to avoid rate limiting
- ✅ Progress updates during sending
- 📊 Summary report after completion
- 🔒 Username validation and error handling

## How It Works

1. User sends `/start` command
2. Bot asks for the message to send
3. Bot asks for Telegram usernames (up to 50)
4. Bot sends messages with a 10-second delay between each
5. Bot sends a completion summary

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (you'll need it for deployment)

### 2. Local Development

```bash
# Clone or download this project
cd telegram-bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and add your bot token
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN

# Run the bot
python bot.py
```

### 3. Deploy on Render

#### Option A: Using render.yaml (Blueprint)

1. Push this code to a GitHub/GitLab repository
2. Log in to [Render](https://render.com)
3. Click "New +" → "Blueprint"
4. Connect your repository
5. Render will detect the `render.yaml` file and create the worker
6. Add your `TELEGRAM_BOT_TOKEN` environment variable in the Render dashboard

#### Option B: Manual Setup

1. Log in to [Render](https://render.com)
2. Click "New +" → "Background Worker"
3. Connect your repository or upload the code
4. Configure:
   - **Name**: `telegram-message-bot`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Add Environment Variable:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token from BotFather
6. Click "Create Background Worker"

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the message sending process |
| `/cancel` | Cancel the current operation |
| `/help` | Show help information |

## Usage Example

1. Send `/start` to the bot
2. Enter your message: `Hello everyone! This is a test message.`
3. Enter usernames: `@user1, @user2, @user3`
4. Wait for the bot to send all messages (with 10s delay between each)
5. Receive the completion summary

## Username Format

You can enter usernames in any of these formats:
- Comma-separated: `@user1, @user2, @user3`
- One per line:
  ```
  @user1
  @user2
  @user3
  ```
- Mixed: `@user1, user2, @user3`

The bot will automatically handle the `@` symbol.

## Configuration

You can modify these constants in `bot.py`:

```python
MAX_USERNAMES = 50      # Maximum number of users to send to
DELAY_SECONDS = 10      # Delay between messages
```

## Important Notes

- The bot must be started by users before it can send them messages
- Users may have privacy settings that prevent receiving messages from bots
- The 10-second delay helps avoid Telegram's rate limiting
- Failed sends are reported in the final summary

## Troubleshooting

### Bot doesn't respond
- Check that `TELEGRAM_BOT_TOKEN` is set correctly
- Check Render logs for errors

### Messages fail to send
- Ensure users have started a conversation with the bot
- Check that usernames are correct
- Some users may have privacy settings blocking bot messages

### Rate limiting
- The 10-second delay is designed to prevent this
- If you still get rate limited, increase `DELAY_SECONDS`

## License

MIT License - Feel free to use and modify as needed.
