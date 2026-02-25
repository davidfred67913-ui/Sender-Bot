#!/usr/bin/env python3
"""
Telegram Message Sender Bot
Uses Telethon (MTProto) to send messages to usernames
"""

import os
import sys
import asyncio

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def log(msg):
    print(msg, flush=True)

log("=" * 60)
log("TELEGRAM BOT STARTING")
log("=" * 60)

# Get environment variables
API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE = os.environ.get("TELEGRAM_PHONE_NUMBER")
SESSION = os.environ.get("SESSION_STRING")

log(f"API_ID present: {bool(API_ID)}")
log(f"API_HASH present: {bool(API_HASH)}")
log(f"PHONE present: {bool(PHONE)}")
log(f"SESSION present: {bool(SESSION)}")

if not all([API_ID, API_HASH, PHONE, SESSION]):
    log("ERROR: Missing required environment variables!")
    log("Please set: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER, SESSION_STRING")
    sys.exit(1)

try:
    API_ID = int(API_ID)
except ValueError:
    log("ERROR: TELEGRAM_API_ID must be a number!")
    sys.exit(1)

# Import telethon
log("Importing Telethon...")
try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    from telethon.tl.types import User
    from telethon.errors import (
        UsernameNotOccupiedError,
        UserPrivacyRestrictedError,
        FloodWaitError
    )
    log("Telethon imported successfully")
except ImportError as e:
    log(f"ERROR: Failed to import Telethon: {e}")
    sys.exit(1)

# Create client
log("Creating Telegram client...")
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
log("Client created")

# User state storage
user_states = {}
user_messages = {}

def parse_usernames(text):
    """Parse usernames from input text."""
    usernames = []
    for line in text.split("\n"):
        for item in line.split(","):
            u = item.strip().lstrip("@").lower()
            if u:
                usernames.append(u)
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for u in usernames:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique

async def send_to_username(username, message):
    """Send message to a username."""
    try:
        entity = await client.get_entity(username)
        if not isinstance(entity, User):
            return {"username": username, "success": False, "error": "Not a user account"}
        await client.send_message(entity.id, message)
        return {"username": username, "success": True, "error": None}
    except UsernameNotOccupiedError:
        return {"username": username, "success": False, "error": "Username not found"}
    except UserPrivacyRestrictedError:
        return {"username": username, "success": False, "error": "User blocked messages"}
    except FloodWaitError as e:
        return {"username": username, "success": False, "error": f"Rate limit: wait {e.seconds}s"}
    except Exception as e:
        return {"username": username, "success": False, "error": str(e)[:40]}

# Event handlers
@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """Handle /start command."""
    try:
        sender = await event.get_sender()
        log(f"/start from {sender.first_name} (ID: {sender.id})")
        await event.reply(
            f"👋 Hello {sender.first_name}!\n\n"
            "I'm a Message Sender Bot.\n\n"
            "📋 Commands:\n"
            "/send - Start sending messages\n"
            "/help - Show help"
        )
    except Exception as e:
        log(f"Error in /start: {e}")

@client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Handle /help command."""
    await event.reply(
        "📖 How to use:\n\n"
        "1. Send /send\n"
        "2. Type your message\n"
        "3. Enter usernames (max 50)\n"
        "4. Wait for completion\n\n"
        "Username format:\n"
        "• @user1, @user2, @user3\n"
        "• Or one per line\n\n"
        "⏱️ 10-second delay between messages"
    )

@client.on(events.NewMessage(pattern="/send"))
async def send_handler(event):
    """Handle /send command."""
    user_id = event.sender_id
    user_states[user_id] = "waiting_message"
    user_messages[user_id] = {}
    log(f"/send from user {user_id}")
    await event.reply("📤 Enter the message you want to send:")

@client.on(events.NewMessage)
async def message_handler(event):
    """Handle regular messages."""
    try:
        user_id = event.sender_id
        text = event.raw_text
        
        # Ignore commands
        if text.startswith("/"):
            return
        
        # Check if user is in a conversation
        if user_id not in user_states:
            return
        
        state = user_states[user_id]
        
        if state == "waiting_message":
            # Store message and ask for usernames
            user_messages[user_id]["message"] = text
            user_states[user_id] = "waiting_usernames"
            await event.reply(
                "✅ Message saved!\n\n"
                "Enter usernames to send to (max 50):\n"
                "Example: @user1, @user2, @user3"
            )
        
        elif state == "waiting_usernames":
            # Parse usernames
            usernames = parse_usernames(text)
            
            if not usernames:
                await event.reply("❌ No valid usernames. Please try again:")
                return
            
            if len(usernames) > 50:
                await event.reply(f"❌ Too many usernames! Max is 50. You entered {len(usernames)}. Try again:")
                return
            
            # Get message and clear state
            message_to_send = user_messages[user_id].get("message", "")
            del user_states[user_id]
            del user_messages[user_id]
            
            log(f"Sending to {len(usernames)} users")
            await event.reply(f"📤 Sending to {len(usernames)} user(s)... Please wait.")
            
            # Send messages with delay
            results = []
            for i, username in enumerate(usernames, 1):
                result = await send_to_username(username, message_to_send)
                results.append(result)
                
                # Progress update every 5 users
                if i % 5 == 0 or i == len(usernames):
                    status = "✅" if result["success"] else "❌"
                    try:
                        await event.reply(f"⏳ Progress: {i}/{len(usernames)} {status}")
                    except:
                        pass
                
                # Delay between messages
                if i < len(usernames):
                    await asyncio.sleep(10)
            
            # Send summary
            successful = sum(1 for r in results if r["success"])
            failed = len(results) - successful
            
            summary = (
                f"✅ Done!\n\n"
                f"📊 Summary:\n"
                f"• Total: {len(results)}\n"
                f"• Successful: {successful}\n"
                f"• Failed: {failed}"
            )
            
            failed_users = [r for r in results if not r["success"]]
            if failed_users:
                summary += "\n\n❌ Failed:"
                for r in failed_users[:5]:
                    summary += f"\n@{r['username']}: {r['error']}"
            
            await event.reply(summary)
            log(f"Completed: {successful} success, {failed} failed")
            
    except Exception as e:
        log(f"Error in message_handler: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function."""
    log("Connecting to Telegram...")
    
    try:
        await client.start()
        log("Connected!")
    except Exception as e:
        log(f"ERROR: Failed to connect: {e}")
        sys.exit(1)
    
    try:
        me = await client.get_me()
        log("=" * 60)
        log(f"✅ LOGGED IN AS: {me.first_name}")
        if me.username:
            log(f"   Username: @{me.username}")
        log(f"   ID: {me.id}")
        log("=" * 60)
        log("🤖 Bot is running! Anyone can now send /start to use it.")
        log("=" * 60)
    except Exception as e:
        log(f"ERROR: Failed to get user info: {e}")
        sys.exit(1)
    
    # Keep running until disconnected
    await client.run_until_disconnected()
    log("Disconnected from Telegram")

# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("\nStopped by user")
    except Exception as e:
        log(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
