#!/usr/bin/env python3
import os
import sys

print("LINE 1: Script started", flush=True)

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE_NUMBER = os.environ.get("TELEGRAM_PHONE_NUMBER")
SESSION_STRING = os.environ.get("SESSION_STRING")

print(f"LINE 2: API_ID={bool(API_ID)}, API_HASH={bool(API_HASH)}, PHONE={bool(PHONE_NUMBER)}, SESSION={bool(SESSION_STRING)}", flush=True)

if not all([API_ID, API_HASH, PHONE_NUMBER, SESSION_STRING]):
    print("ERROR: Missing environment variables", flush=True)
    sys.exit(1)

print("LINE 3: Importing telethon...", flush=True)

try:
    import asyncio
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    from telethon.tl.types import User
    from telethon.errors import UsernameNotOccupiedError, UserPrivacyRestrictedError, FloodWaitError
    print("LINE 4: Telethon imported successfully", flush=True)
except Exception as e:
    print(f"ERROR importing telethon: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("LINE 5: Creating client...", flush=True)

try:
    client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
    print("LINE 6: Client created", flush=True)
except Exception as e:
    print(f"ERROR creating client: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

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
    try:
        sender = await event.get_sender()
        print(f"/start from {sender.first_name}", flush=True)
        await event.reply(f"Hello {sender.first_name}!\n\n/send - Send messages\n/help - Help")
    except Exception as e:
        print(f"Error in start: {e}", flush=True)

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
    print("LINE 7: Connecting to Telegram...", flush=True)
    
    try:
        await client.connect()
        print("LINE 8: Connected", flush=True)
    except Exception as e:
        print(f"ERROR connecting: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return
    
    try:
        authorized = await client.is_user_authorized()
        print(f"LINE 9: Authorized={authorized}", flush=True)
    except Exception as e:
        print(f"ERROR checking auth: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return
    
    if not authorized:
        print("ERROR: Not authenticated. SESSION_STRING may be invalid.", flush=True)
        return
    
    try:
        me = await client.get_me()
        print(f"LINE 10: Logged in as {me.first_name} (@{me.username})", flush=True)
    except Exception as e:
        print(f"ERROR getting me: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return
    
    print("LINE 11: Bot is running! Waiting for messages...", flush=True)
    
    try:
        await client.run_until_disconnected()
    except Exception as e:
        print(f"ERROR in run_until_disconnected: {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    print("LINE 12: Disconnected", flush=True)

print("LINE 13: About to run main()", flush=True)

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Stopped by user", flush=True)
    except Exception as e:
        print(f"FATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    print("LINE 14: Script ending", flush=True)
