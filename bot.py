#!/usr/bin/env python3
"""
Telegram UserBot for sending messages to usernames
Uses MTProto API (Telethon) - requires a real Telegram account
Deployed on Render as a Background Worker

IMPORTANT: This uses a REAL Telegram account (phone number), not a bot token.
"""

import os
import asyncio
import logging
from typing import List, Optional

from telethon import TelegramClient, events
from telethon.tl.types import User
from telethon.errors import (
    UsernameNotOccupiedError,
    UsernameInvalidError,
    FloodWaitError,
    UserPrivacyRestrictedError,
    PeerIdInvalidError,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Configuration
MAX_USERNAMES = 50
DELAY_SECONDS = 10

# Get credentials from environment
API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE_NUMBER = os.environ.get("TELEGRAM_PHONE_NUMBER")
SESSION_NAME = os.environ.get("SESSION_NAME", "userbot_session")

# Validate config
if not all([API_ID, API_HASH, PHONE_NUMBER]):
    raise ValueError(
        "Missing required environment variables:\n"
        "TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER"
    )

# Create client
client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)


async def resolve_username_to_id(username: str) -> Optional[int]:
    """Convert username to user ID using MTProto API."""
    try:
        # Remove @ if present
        username = username.lstrip("@").strip()
        
        # Get entity (this resolves username to user object)
        entity = await client.get_entity(username)
        
        if isinstance(entity, User):
            return entity.id
        else:
            logger.warning(f"@{username} is not a user (might be a channel/group)")
            return None
            
    except UsernameNotOccupiedError:
        logger.error(f"Username @{username} does not exist")
        return None
    except UsernameInvalidError:
        logger.error(f"Username @{username} is invalid")
        return None
    except Exception as e:
        logger.error(f"Error resolving @{username}: {e}")
        return None


async def send_message_to_username(username: str, message: str) -> dict:
    """Send message to a username. Returns result dict."""
    result = {
        "username": username,
        "success": False,
        "error": None,
        "user_id": None,
    }
    
    try:
        # Resolve username to ID
        user_id = await resolve_username_to_id(username)
        
        if not user_id:
            result["error"] = "Username not found or invalid"
            return result
        
        result["user_id"] = user_id
        
        # Send message
        await client.send_message(user_id, message)
        result["success"] = True
        logger.info(f"Message sent to @{username} (ID: {user_id})")
        
    except UserPrivacyRestrictedError:
        result["error"] = "User has privacy settings that prevent receiving messages"
        logger.error(f"Privacy restriction for @{username}")
        
    except FloodWaitError as e:
        result["error"] = f"Rate limited. Wait {e.seconds} seconds"
        logger.error(f"Flood wait for @{username}: {e.seconds}s")
        
    except PeerIdInvalidError:
        result["error"] = "Invalid user ID (user may have deleted account)"
        logger.error(f"Peer ID invalid for @{username}")
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Failed to send to @{username}: {e}")
    
    return result


async def send_messages_to_list(usernames: List[str], message: str, progress_callback=None) -> List[dict]:
    """Send messages to a list of usernames with delay."""
    results = []
    
    for i, username in enumerate(usernames, 1):
        # Send message
        result = await send_message_to_username(username, message)
        results.append(result)
        
        # Progress callback
        if progress_callback:
            await progress_callback(i, len(usernames), result)
        
        # Delay between messages (except after last)
        if i < len(usernames):
            await asyncio.sleep(DELAY_SECONDS)
    
    return results


def parse_usernames(text: str) -> List[str]:
    """Parse usernames from input text."""
    # Split by commas or newlines
    raw_list = []
    for line in text.split("\n"):
        for item in line.split(","):
            raw_list.append(item.strip())
    
    # Clean usernames
    usernames = []
    for username in raw_list:
        username = username.strip()
        if username.startswith("@"):
            username = username[1:]
        if username:
            usernames.append(username.lower())
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for u in usernames:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    
    return unique


async def generate_summary(results: List[dict]) -> str:
    """Generate a summary of the sending operation."""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    summary = [
        "✅ <b>All messages processed!</b>",
        "",
        "📊 <b>Summary:</b>",
        f"• Total: {total}",
        f"• Successful: {successful}",
        f"• Failed: {failed}",
    ]
    
    # List failed users
    failed_users = [r for r in results if not r["success"]]
    if failed_users:
        summary.extend(["", "❌ <b>Failed sends:</b>"])
        for r in failed_users:
            summary.append(f"• @{r['username']}: {r['error']}")
    
    return "\n".join(summary)


# ============== Event Handlers ==============

@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """Handle /start command."""
    sender = await event.get_sender()
    await event.reply(
        f"👋 Hello, {sender.first_name}!\n\n"
        "I'm a Message Sender Bot. I can send messages to any Telegram user by username.\n\n"
        "📋 <b>Commands:</b>\n"
        "/send - Start sending messages\n"
        "/help - Show help\n\n"
        "⚠️ <b>Note:</b> I use a real Telegram account to resolve usernames.",
        parse_mode="html"
    )


@client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Handle /help command."""
    await event.reply(
        "📖 <b>How to use:</b>\n\n"
        "1. Send /send to start\n"
        "2. Type your message\n"
        "3. Enter usernames (max 50)\n"
        "4. Wait for completion\n\n"
        "<b>Username format:</b>\n"
        "• @username1, @username2\n"
        "• Or one per line\n\n"
        "<b>Commands:</b>\n"
        "/start - Start the bot\n"
        "/send - Send messages\n"
        "/help - Show this help\n\n"
        "⏱️ 10-second delay between messages",
        parse_mode="html"
    )


# Conversation state storage (simple dict, per-user)
user_states = {}
user_messages = {}


@client.on(events.NewMessage(pattern="/send"))
async def send_handler(event):
    """Handle /send command - start conversation."""
    user_id = event.sender_id
    user_states[user_id] = "waiting_message"
    user_messages[user_id] = {}
    
    await event.reply(
        "📤 Let's send a message!\n\n"
        "Please type the message you want to send:"
    )


@client.on(events.NewMessage)
async def message_handler(event):
    """Handle user messages based on state."""
    user_id = event.sender_id
    
    # Ignore commands
    if event.raw_text.startswith("/"):
        return
    
    # Check if user is in a conversation
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    text = event.raw_text
    
    if state == "waiting_message":
        # Store message and ask for usernames
        user_messages[user_id]["message"] = text
        user_states[user_id] = "waiting_usernames"
        
        await event.reply(
            "✅ Message saved!\n\n"
            f"Now enter the usernames to send to (max {MAX_USERNAMES}):\n"
            "• Separate with commas or new lines\n"
            "• Example: @user1, @user2, @user3"
        )
    
    elif state == "waiting_usernames":
        # Parse and validate usernames
        usernames = parse_usernames(text)
        
        if len(usernames) == 0:
            await event.reply(
                "❌ No valid usernames found. Please enter at least one username:"
            )
            return
        
        if len(usernames) > MAX_USERNAMES:
            await event.reply(
                f"❌ Too many usernames! You provided {len(usernames)}, "
                f"but the maximum is {MAX_USERNAMES}.\n\n"
                f"Please enter {MAX_USERNAMES} or fewer usernames:"
            )
            return
        
        # Clear state
        del user_states[user_id]
        message_to_send = user_messages[user_id].get("message", "")
        del user_messages[user_id]
        
        # Start sending
        await event.reply(
            f"📤 Sending to {len(usernames)} user(s)...\n"
            f"⏱️ {DELAY_SECONDS}-second delay between messages.\n"
            f"Please wait..."
        )
        
        # Progress callback
        async def progress(current, total, result):
            if current % 5 == 0 or current == total:
                status = "✅" if result["success"] else "❌"
                await event.reply(
                    f"⏳ Progress: {current}/{total} - @{result['username']} {status}"
                )
        
        # Send messages
        results = await send_messages_to_list(usernames, message_to_send, progress)
        
        # Send summary
        summary = await generate_summary(results)
        await event.reply(summary, parse_mode="html")


async def main():
    """Main function to start the client."""
    logger.info("Starting Telegram UserBot...")
    
    # Start the client
    await client.start(phone=PHONE_NUMBER)
    
    # Get and log the user info
    me = await client.get_me()
    logger.info(f"Logged in as: {me.first_name} (@{me.username}, ID: {me.id})")
    
    # Run until disconnected
    logger.info("Bot is running! Waiting for messages...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    # Run the main function
    client.loop.run_until_complete(main())
t update.message.reply_text(summary, parse_mode="HTML")
    
    context.user_data.clear()
    return ConversationHandler.END


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show registered users."""
    users = load_registered_users()
    
    if not users:
        await update.message.reply_text(
            "📭 No registered users yet.\n"
            "Share your bot link so people can start it!"
        )
        return
    
    user_list = []
    for user_id, data in users.items():
        username = data.get("username")
        first_name = data.get("first_name", "Unknown")
        if username:
            user_list.append(f"• @{username} ({first_name})")
        else:
            user_list.append(f"• {first_name} (ID: {user_id})")
    
    await update.message.reply_text(
        f"📋 <b>Registered Users ({len(users)}):</b>\n\n"
        + "\n".join(user_list),
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    await update.message.reply_text(
        "📖 <b>Bot Commands:</b>\n\n"
        "/start - Register yourself and start the bot\n"
        "/send - Start sending messages to users\n"
        "/users - List all registered users\n"
        "/help - Show this help message\n"
        "/cancel - Cancel current operation\n\n"
        "<b>How to send messages:</b>\n"
        "1. Send /send\n"
        "2. Type your message\n"
        "3. Enter usernames (or type ALL)\n"
        "4. Wait for completion\n\n"
        "<b>Important:</b>\n"
        "• Users must /start the bot before receiving messages\n"
        "• Max 50 users per batch\n"
        "• 10-second delay between messages\n"
        "• Use @username format or type ALL",
        parse_mode="HTML"
    )


def main() -> None:
    """Start the bot."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("send", send_command)],
        states={
            MESSAGE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)
            ],
            USERNAME_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_usernames)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("help", help_command))
    
    logger.info("Bot started! Waiting for messages...")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
