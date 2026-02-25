#!/usr/bin/env python3
"""
Telegram UserBot for sending messages to usernames
Uses MTProto API (Telethon) - requires a real Telegram account
"""

import os
import asyncio
import logging
import sys
import traceback
from typing import List, Optional

from telethon import TelegramClient, events
from telethon.tl.types import User
from telethon.errors import (
    UsernameNotOccupiedError,
    UsernameInvalidError,
    FloodWaitError,
    UserPrivacyRestrictedError,
    PeerIdInvalidError,
    SessionPasswordNeededError,
    AuthKeyUnregisteredError,
)
from telethon.sessions import StringSession

# Setup logging - MUST go to stdout for Render
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Force stdout flush for Render
sys.stdout.reconfigure(line_buffering=True)

# Configuration
MAX_USERNAMES = 50
DELAY_SECONDS = 10

print("=" * 60, flush=True)
print("BOT STARTING UP...", flush=True)
print("=" * 60, flush=True)

# Get credentials from environment
API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE_NUMBER = os.environ.get("TELEGRAM_PHONE_NUMBER")
SESSION_STRING = os.environ.get("SESSION_STRING")

print(f"API_ID present: {bool(API_ID)}", flush=True)
print(f"API_HASH present: {bool(API_HASH)}", flush=True)
print(f"PHONE_NUMBER present: {bool(PHONE_NUMBER)}", flush=True)
print(f"SESSION_STRING present: {bool(SESSION_STRING)}", flush=True)

# Validate config
if not API_ID:
    print("ERROR: TELEGRAM_API_ID is not set!", flush=True)
    sys.exit(1)
if not API_HASH:
    print("ERROR: TELEGRAM_API_HASH is not set!", flush=True)
    sys.exit(1)
if not PHONE_NUMBER:
    print("ERROR: TELEGRAM_PHONE_NUMBER is not set!", flush=True)
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    print("ERROR: TELEGRAM_API_ID must be a number!", flush=True)
    sys.exit(1)

# Create client
if SESSION_STRING:
    print("Using SESSION_STRING from environment", flush=True)
    session = StringSession(SESSION_STRING)
else:
    print("Using file-based session", flush=True)
    session = "userbot_session"

client = TelegramClient(session, API_ID, API_HASH)

# User state storage
user_states = {}
user_messages = {}


def parse_usernames(text: str) -> List[str]:
    """Parse usernames from input text."""
    raw_list = []
    for line in text.split("\n"):
        for item in line.split(","):
            raw_list.append(item.strip())
    
    usernames = []
    for username in raw_list:
        username = username.strip()
        if username.startswith("@"):
            username = username[1:]
        if username:
            usernames.append(username.lower())
    
    # Remove duplicates
    seen = set()
    unique = []
    for u in usernames:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    
    return unique


async def resolve_and_send(username: str, message: str) -> dict:
    """Resolve username and send message."""
    result = {"username": username, "success": False, "error": None}
    
    try:
        clean_username = username.lstrip("@").strip()
        if not clean_username:
            result["error"] = "Empty username"
            return result
        
        print(f"Resolving @{clean_username}...", flush=True)
        entity = await client.get_entity(clean_username)
        
        if not isinstance(entity, User):
            result["error"] = "Not a user (might be channel/group)"
            return result
        
        await client.send_message(entity.id, message)
        result["success"] = True
        print(f"✅ Sent to @{clean_username}", flush=True)
        
    except UsernameNotOccupiedError:
        result["error"] = "Username does not exist"
    except UsernameInvalidError:
        result["error"] = "Invalid username"
    except UserPrivacyRestrictedError:
        result["error"] = "User privacy settings block messages"
    except FloodWaitError as e:
        result["error"] = f"Rate limited, wait {e.seconds}s"
    except Exception as e:
        result["error"] = str(e)[:50]
        print(f"Error sending to @{username}: {e}", flush=True)
    
    return result


# ============== Event Handlers ==============

@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """Handle /start command."""
    try:
        sender = await event.get_sender()
        print(f"/start from {sender.first_name} (ID: {sender.id})", flush=True)
        
        await event.reply(
            f"👋 Hello, {sender.first_name}!\n\n"
            "I'm a Message Sender Bot. I can send messages to any Telegram user by username.\n\n"
            "📋 Commands:\n"
            "/send - Start sending messages\n"
            "/help - Show help",
        )
    except Exception as e:
        print(f"Error in start_handler: {e}", flush=True)


@client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Handle /help command."""
    try:
        await event.reply(
            "📖 How to use:\n\n"
            "1. Send /send to start\n"
            "2. Type your message\n"
            "3. Enter usernames (max 50)\n"
            "4. Wait for completion\n\n"
            "Username format:\n"
            "• @username1, @username2\n"
            "• Or one per line\n\n"
            "⏱️ 10-second delay between messages"
        )
    except Exception as e:
        print(f"Error in help_handler: {e}", flush=True)


@client.on(events.NewMessage(pattern="/send"))
async def send_handler(event):
    """Handle /send command."""
    try:
        user_id = event.sender_id
        user_states[user_id] = "waiting_message"
        user_messages[user_id] = {}
        
        print(f"/send from user {user_id}", flush=True)
        
        await event.reply("📤 Let's send a message!\n\nPlease type your message:")
    except Exception as e:
        print(f"Error in send_handler: {e}", flush=True)


@client.on(events.NewMessage)
async def message_handler(event):
    """Handle user messages."""
    try:
        user_id = event.sender_id
        text = event.raw_text
        
        # Ignore commands
        if text.startswith("/"):
            return
        
        if user_id not in user_states:
            return
        
        state = user_states[user_id]
        
        if state == "waiting_message":
            user_messages[user_id]["message"] = text
            user_states[user_id] = "waiting_usernames"
            
            await event.reply(
                "✅ Message saved!\n\n"
                f"Enter usernames (max {MAX_USERNAMES}):\n"
                "Example: @user1, @user2, @user3"
            )
        
        elif state == "waiting_usernames":
            usernames = parse_usernames(text)
            
            if len(usernames) == 0:
                await event.reply("❌ No valid usernames. Try again:")
                return
            
            if len(usernames) > MAX_USERNAMES:
                await event.reply(f"❌ Too many! Max is {MAX_USERNAMES}. Try again:")
                return
            
            message_to_send = user_messages[user_id].get("message", "")
            del user_states[user_id]
            del user_messages[user_id]
            
            await event.reply(f"📤 Sending to {len(usernames)} user(s)... Please wait.")
            
            # Send messages
            results = []
            for i, username in enumerate(usernames, 1):
                result = await resolve_and_send(username, message_to_send)
                results.append(result)
                
                if i % 5 == 0 or i == len(usernames):
                    status = "✅" if result["success"] else "❌"
                    try:
                        await event.reply(f"Progress: {i}/{len(usernames)} {status}")
                    except:
                        pass
                
                if i < len(usernames):
                    await asyncio.sleep(DELAY_SECONDS)
            
            # Summary
            successful = sum(1 for r in results if r["success"])
            failed = len(results) - successful
            
            summary = f"✅ Done!\n\n📊 Summary:\n• Total: {len(results)}\n• Successful: {successful}\n• Failed: {failed}"
            
            failed_users = [r for r in results if not r["success"]]
            if failed_users:
                summary += "\n\n❌ Failed:\n"
                for r in failed_users[:5]:  # Show first 5
                    summary += f"• @{r['username']}: {r['error']}\n"
            
            await event.reply(summary)
            
    except Exception as e:
        print(f"Error in message_handler: {e}", flush=True)
        traceback.print_exc()


async def main():
    """Main function."""
    print("=" * 60, flush=True)
    print("CONNECTING TO TELEGRAM...", flush=True)
    print("=" * 60, flush=True)
    
    try:
        await client.connect()
        print("Connected to Telegram servers", flush=True)
        
        # Check if authorized
        if await client.is_user_authorized():
            print("✅ Already authenticated!", flush=True)
        else:
            print("❌ NOT AUTHENTICATED!", flush=True)
            print("You need to set SESSION_STRING environment variable.", flush=True)
            print("Run 'python generate_session.py' locally to get it.", flush=True)
            await client.disconnect()
            # Keep running so Render doesn't restart loop
            while True:
                print("Waiting for SESSION_STRING... Check logs above.", flush=True)
                await asyncio.sleep(60)
            return
        
        me = await client.get_me()
        print("=" * 60, flush=True)
        print(f"✅ LOGGED IN AS: {me.first_name}", flush=True)
        if me.username:
            print(f"   Username: @{me.username}", flush=True)
        print(f"   ID: {me.id}", flush=True)
        print("=" * 60, flush=True)
        print("🤖 Bot is running! Send /start to test.", flush=True)
        print("=" * 60, flush=True)
        
        # Keep running
        await client.run_until_disconnected()
        
    except AuthKeyUnregisteredError:
        print("=" * 60, flush=True)
        print("❌ AUTHENTICATION FAILED!", flush=True)
        print("Your SESSION_STRING is invalid or expired.", flush=True)
        print("Generate a new one with: python generate_session.py", flush=True)
        print("=" * 60, flush=True)
        # Keep process alive to see error
        while True:
            await asyncio.sleep(60)
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}", flush=True)
        traceback.print_exc()
        # Keep process alive to see error
        while True:
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped by user", flush=True)
    except Exception as e:
        print(f"Bot crashed: {e}", flush=True)
        traceback.print_exc()
