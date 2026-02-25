#!/usr/bin/env python3
"""Entry point for Render Background Worker"""
import os
import sys

print("=" * 50, flush=True)
print("MAIN.PY STARTED", flush=True)
print("=" * 50, flush=True)
print(f"Python version: {sys.version}", flush=True)
print(f"Working directory: {os.getcwd()}", flush=True)
print(f"Files: {os.listdir('.')}", flush=True)
print("=" * 50, flush=True)

# Now run the actual bot
exec(open('bot.py').read())
