#!/bin/bash

# Start Korean Learning Bot services
echo "Starting bot and API services..."

# Start uvicorn API server in background
echo "Starting Uvicorn API server..."
nohup uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
echo "Uvicorn API server started (PID: $!)"

# Start Telegram bot in background
echo "Starting Telegram bot..."
nohup uv run python3 -m src.tgbot.bot > bot.log 2>&1 &
echo "Telegram bot started (PID: $!)"

echo "All services started. Check uvicorn.log and bot.log for output."