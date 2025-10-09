#!/bin/bash

# Stop Korean Learning Bot services
echo "Stopping bot and API services..."

# Kill the Telegram bot
pkill -f -9 "src.tgbot.bot"
if [ $? -eq 0 ]; then
    echo "Telegram bot stopped"
else
    echo "No Telegram bot process found or already stopped"
fi

# Kill uvicorn API server
pkill -f -9 "uvicorn"
if [ $? -eq 0 ]; then
    echo "Uvicorn API server stopped"
else
    echo "No uvicorn process found or already stopped"
fi

echo "All services stopped"