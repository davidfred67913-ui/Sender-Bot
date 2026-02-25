#!/usr/bin/env python3
import os
import sys
import asyncio

print("BOT STARTING", flush=True)

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE_NUMBER = os.environ.get("TELEGRAM_PHONE_NUMBER")
SESSION_STRING = os.environ.get("SESSION_STRING")

print(f"API_ID: {bool(API_ID)}", flush=True)
print(f"API_HASH: {bool(API_HASH)}", flush=True)
print(f"PHONE: {bool(PHONE_NUMBER)}", flush=True)
print(f"SESSION: {bool(SESSION_STRING)}", flush=True)

if not all([API_ID, API_HASH, PHONE_NUMBER, SESSION_STRING]):
    print("MISSING ENV VARS", flush=True)
    sys.exit(1)

try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    from telethon.tl.types import User
    from telethon.errors import UsernameNotOccupiedError, UserPrivacyRestrictedError, FloodWaitError
    print("Telethon imported", flush=True)
except Exception as e:
    print(f"Import error: {e}", flush=True)
    sys.exit(1)

client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
user_states = {}
user_messages = {}

def parse_usernames(text):
    usernames = []
    for line in text.split("\n"):
        for item in line.split(","):
            u = item.strip().lstrip("@").lower()
            if u:
                usernames.append(u)
    return list(dict.fromkeys(usernames))

async def send_to_username(username, message):
    try:
        entity = await client.get_entity(username)
        if not isinstance(entity, User):
            return {"username": username, "success": False, "error": "Not a user"}
        await client.send_message(entity.id, message)
        return {"username": username, "success": True, "error": None}
    except UsernameNotOccupiedError:
        return {"username": username, "success": False, "error": "User not found"}
    except UserPrivacyRestrictedError:
        return {"username": username, "success": False, "error": "Privacy blocked"}
    except FloodWaitError as e:
        return {"username": username, "success": False, "error": f"Rate limit {e.seconds}s"}
    except Exception as e:
        return {"username": username, "success": False, "error": str(e)[:30]}

@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    sender = await event.get_sender()
    await event.reply(f"Hello {sender.first_name}!\n\n/send - Send messages\n/help - Help")

@client.on(events.NewMessage(pattern="/help"))
async def help_cmd(event):
    await event.reply("How to use:\n1. Send /send\n2. Type message\n3. Enter usernames\n\nMax 50 users, 10s delay")

@client.on(events.NewMessage(pattern="/send"))
async def send_cmd(event):
    user_states[event.sender_id] = "waiting_msg"
    user_messages[event.sender_id] = {}
    await event.reply("Enter your message:")

@client.on(events.NewMessage)
async def handle_msg(event):
    uid = event.sender_id
    text = event.raw_text
    
    if text.startswith("/"):
        return
    
    if uid not in user_states:
        return
    
    state = user_states[uid]
    
    if state == "waiting_msg":
        user_messages[uid]["msg"] = text
        user_states[uid] = "waiting_users"
        await event.reply("Enter usernames (max 50):\nExample: @user1, @user2")
    
    elif state == "waiting_users":
        usernames = parse_usernames(text)
        
        if not usernames:
            await event.reply("No valid usernames. Try again:")
            return
        
        if len(usernames) > 50:
            await event.reply("Too many! Max 50. Try again:")
            return
        
        msg = user_messages[uid].get("msg", "")
        del user_states[uid]
        del user_messages[uid]
        
        await event.reply(f"Sending to {len(usernames)} users...")
        
        results = []
        for i, username in enumerate(usernames, 1):
            result = await send_to_username(username, msg)
            results.append(result)
            
            if i % 5 == 0 or i == len(usernames):
                status = "OK" if result["success"] else "FAIL"
                await event.reply(f"Progress: {i}/{len(usernames)} {status}")
            
            if i < len(usernames):
                await asyncio.sleep(10)
        
        success = sum(1 for r in results if r["success"])
        failed = len(results) - success
        
        summary = f"Done!\nTotal: {len(results)}\nSuccess: {success}\nFailed: {failed}"
        
        fails = [r for r in results if not r["success"]]
        if fails:
            summary += "\n\nFailed:"
            for r in fails[:5]:
                summary += f"\n@{r['username']}: {r['error']}"
        
        await event.reply(summary)

async def main():
    print("Connecting...", flush=True)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("NOT AUTHENTICATED - Check SESSION_STRING", flush=True)
        return
    
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username})", flush=True)
    print("Bot running! Send /start to test.", flush=True)
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
