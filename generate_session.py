#!/usr/bin/env python3
"""
Generate SESSION_STRING for Render deployment.
Run this ONCE on your local machine, then add the output to Render env vars.
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

print("=" * 60)
print("SESSION STRING GENERATOR")
print("=" * 60)
print()

API_ID = input("Enter your TELEGRAM_API_ID: ").strip()
API_HASH = input("Enter your TELEGRAM_API_HASH: ").strip()
PHONE = input("Enter your phone number (with +, e.g., +1234567890): ").strip()

print()
print("Generating session...")
print()

async def generate():
    client = TelegramClient(StringSession(), int(API_ID), API_HASH)
    await client.start(phone=PHONE)
    
    session_string = client.session.save()
    me = await client.get_me()
    
    print("=" * 60)
    print("✅ SUCCESS!")
    print("=" * 60)
    print()
    print("SESSION_STRING (copy this exactly):")
    print("-" * 60)
    print(session_string)
    print("-" * 60)
    print()
    print(f"Logged in as: {me.first_name} (@{me.username})")
    print()
    print("Add this to your Render Environment Variables:")
    print("  SESSION_STRING = (the string above)")
    print("  TELEGRAM_API_ID = " + API_ID)
    print("  TELEGRAM_API_HASH = " + API_HASH)
    print("  TELEGRAM_PHONE_NUMBER = " + PHONE)
    print()
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(generate())
