#!/usr/bin/env python3
"""
Telegram Bot for sending messages to multiple users
Deployed on Render as a Background Worker
"""

import os
import asyncio
import logging
from typing import List

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
MESSAGE_INPUT = 1
USERNAME_INPUT = 2

# Configuration
MAX_USERNAMES = 50
DELAY_SECONDS = 10


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask for the message."""
    await update.message.reply_text(
        "👋 Welcome to the Message Sender Bot!\n\n"
        "I'll help you send messages to multiple Telegram users.\n\n"
        "Please type the message you want to send:"
    )
    return MESSAGE_INPUT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "❌ Operation cancelled. Send /start to begin again."
    )
    context.user_data.clear()
    return ConversationHandler.END


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the message and ask for usernames."""
    message_text = update.message.text
    context.user_data["message"] = message_text
    
    await update.message.reply_text(
        "✅ Message received!\n\n"
        f"Now, please enter the Telegram usernames to send this message to.\n"
        f"• You can enter up to {MAX_USERNAMES} usernames\n"
        f"• Separate usernames with commas or put each on a new line\n"
        f"• Include or exclude the @ symbol (both work)\n\n"
        f"Example: @user1, @user2, @user3"
    )
    return USERNAME_INPUT


def parse_usernames(text: str) -> List[str]:
    """Parse usernames from input text."""
    # Split by commas or newlines
    raw_list = []
    for line in text.split("\n"):
        for item in line.split(","):
            raw_list.append(item.strip())
    
    # Clean usernames (remove @ if present)
    usernames = []
    for username in raw_list:
        username = username.strip()
        if username.startswith("@"):
            username = username[1:]
        if username:
            usernames.append(username)
    
    return usernames


async def receive_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive usernames, validate, and send messages."""
    text = update.message.text
    usernames = parse_usernames(text)
    
    # Validate username count
    if len(usernames) == 0:
        await update.message.reply_text(
            "❌ No valid usernames found. Please enter at least one username:"
        )
        return USERNAME_INPUT
    
    if len(usernames) > MAX_USERNAMES:
        await update.message.reply_text(
            f"❌ Too many usernames! You provided {len(usernames)}, "
            f"but the maximum allowed is {MAX_USERNAMES}.\n\n"
            f"Please enter {MAX_USERNAMES} or fewer usernames:"
        )
        return USERNAME_INPUT
    
    # Store usernames and start sending
    context.user_data["usernames"] = usernames
    message_to_send = context.user_data.get("message", "")
    
    await update.message.reply_text(
        f"📤 Starting to send messages to {len(usernames)} user(s)...\n"
        f"⏱️ There will be a {DELAY_SECONDS}-second delay between each message.\n"
        f"Please wait..."
    )
    
    # Send messages with delay
    successful = 0
    failed = 0
    failed_users = []
    
    for i, username in enumerate(usernames, 1):
        try:
            # Send message to user
            await context.bot.send_message(
                chat_id=f"@{username}",
                text=message_to_send
            )
            successful += 1
            logger.info(f"Message sent to @{username}")
            
        except Exception as e:
            failed += 1
            failed_users.append(username)
            logger.error(f"Failed to send to @{username}: {e}")
        
        # Show progress every 5 users or on last user
        if i % 5 == 0 or i == len(usernames):
            await update.message.reply_text(
                f"⏳ Progress: {i}/{len(usernames)} messages sent..."
            )
        
        # Delay between messages (except after the last one)
        if i < len(usernames):
            await asyncio.sleep(DELAY_SECONDS)
    
    # Send completion summary
    summary = (
        f"✅ <b>All messages sent!</b>\n\n"
        f"📊 <b>Summary:</b>\n"
        f"• Total users: {len(usernames)}\n"
        f"• Successful: {successful}\n"
        f"• Failed: {failed}"
    )
    
    if failed_users:
        summary += f"\n\n❌ <b>Failed to send to:</b>\n"
        summary += ", ".join([f"@{u}" for u in failed_users])
        summary += "\n\n<i>Note: Users may have privacy settings that prevent receiving messages from bots, or the username may not exist.</i>"
    
    await update.message.reply_text(summary, parse_mode="HTML")
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    await update.message.reply_text(
        "📖 <b>How to use this bot:</b>\n\n"
        "1. Send /start to begin\n"
        "2. Enter the message you want to send\n"
        "3. Enter the usernames (up to 50)\n"
        "4. The bot will send messages with a 10-second delay between each\n\n"
        "<b>Commands:</b>\n"
        "/start - Start sending messages\n"
        "/cancel - Cancel the current operation\n"
        "/help - Show this help message",
        parse_mode="HTML"
    )


def main() -> None:
    """Start the bot."""
    # Get token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Conversation handler for the message sending flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
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
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    
    # Log startup
    logger.info("Bot started! Waiting for messages...")
    
    # Run the bot until Ctrl-C is pressed
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
