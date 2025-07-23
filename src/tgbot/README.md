# Telegram Bot Package

## Purpose
Aiogram-based Telegram bot that serves as the frontend interface for the Korean learning chatbot. Handles user interactions, message routing, and response formatting.

## Key Components
- **bot.py**: Main bot application with startup, middleware, and polling configuration
- **handlers/**: Message and callback handlers organized by functionality
- **keyboards/**: Inline keyboards for user interaction
- **middlewares/**: Custom middleware for configuration and database integration
- **services/**: Broadcasting and utility services
- **filters/**: Custom filters for message processing
- **misc/**: Bot states and utility functions

## Handler Structure
- **user.py**: User registration and basic interactions
- **chat.py**: Main chat message processing and API communication
- **admin.py**: Administrative functions
- **help.py**: Help and information commands
- **vocab.py**: Vocabulary-related features

## Dependencies
- **src/api/**: Sends user messages to API for processing
- **src/db/**: User management and registration
- **src/utils/**: Message formatting utilities
- **src/config/**: Bot configuration and settings

## Key Features
- User registration and authentication
- Message forwarding to API backend
- Response formatting with Telegram HTML support
- Admin broadcasting capabilities
- Custom keyboards for enhanced UX
- Redis/Memory storage for FSM states

## Usage
Start the bot:
```bash
docker compose up tgbot
```

Available commands:
- `/start`: Bot initialization and user registration
- `/help`: Display help information
- `/menu`: Show main menu
- `/vocab`: Access vocabulary features

## Message Flow
1. User sends message to Telegram bot
2. Bot forwards to API via `/invoke` endpoint
3. API processes through LLM agents
4. Bot receives formatted response and displays to user