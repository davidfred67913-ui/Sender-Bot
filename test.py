#!/usr/bin/env python3
"""Quick test to check if environment variables are set correctly"""
import os
import sys

print("=" * 50)
print("ENVIRONMENT VARIABLE TEST")
print("=" * 50)

vars_to_check = [
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH", 
    "TELEGRAM_PHONE_NUMBER",
    "SESSION_STRING"
]

all_good = True
for var in vars_to_check:
    value = os.environ.get(var)
    if value:
        # Mask the value for security
        masked = value[:5] + "..." + value[-5:] if len(value) > 10 else "***"
        print(f"✅ {var}: {masked} (length: {len(value)})")
    else:
        print(f"❌ {var}: NOT SET")
        all_good = False

print("=" * 50)

if all_good:
    print("All environment variables are set!")
    print("Testing Telethon import...")
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        print("✅ Telethon imported successfully")
    except Exception as e:
        print(f"❌ Telethon import failed: {e}")
        sys.exit(1)
else:
    print("❌ Some environment variables are missing!")
    print("Please set them in Render dashboard.")
    sys.exit(1)
