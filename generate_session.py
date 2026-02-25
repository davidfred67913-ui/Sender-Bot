#!/usr/bin/env python3
"""
Helper script to generate SESSION_STRING for Render deployment.
Run this locally ONCE, then add the output to Render environment variables.
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Get credentials
API_ID = input("Enter your TELEGRAM_API_ID: ").strip()
API_HASH = input("Enter your TELEGRAM_API_HASH: ").strip()
PHONE_NUMBER = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()

async def generate_session():
    """Generate a session string for Render deployment."""
    print("\n" + "=" * 50)
    print("Generating SESSION_STRING...")
    print("=" * 50 + "\n")
    
    # Create client with StringSession
    client = TelegramClient(StringSession(), int(API_ID), API_HASH)
    
    await client.start(phone=PHONE_NUMBER)
    
    # Get the session string
    session_string = client.session.save()
    
    print("\n" + "=" * 50)
    print("✅ SUCCESS! Copy this SESSION_STRING:")
    print("=" * 50)
    print(session_string)
    print("=" * 50)
    print("\nAdd this to your Render environment variables as:")
    print("SESSION_STRING = (the string above)")
    print("\nAlso add these environment variables:")
    print(f"TELEGRAM_API_ID = {API_ID}")
    print(f"TELEGRAM_API_HASH = {API_HASH}")
    print(f"TELEGRAM_PHONE_NUMBER = {PHONE_NUMBER}")
    print("=" * 50)
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_session())
