#!/bin/bash
set -e

echo "=== Starting Telegram Bot ==="
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la

echo ""
echo "Checking Python..."
python --version

echo ""
echo "Running bot.py..."
exec python bot.py
