# Telegram Bot Module

This module implements the Telegram bot interface for the Korean Learning Bot, handling user interactions and providing language learning features through an intuitive chat interface.

## Core Features

- User registration and session management
- Message handling and routing to API endpoints
- Korean vocabulary lookup with detailed examples
- Interactive pagination for browsing examples
- Command system for accessing different features
- Admin commands for maintenance and monitoring

## Implementation Details

The module is organized into several components:

1. **bot.py**: Main entry point that configures and starts the bot
   - Sets up command menu
   - Configures middleware and handlers
   - Initializes the bot with Telegram API

2. **handlers/**: Message and command handlers
   - chat.py: Processes regular chat messages and routes to API
   - vocab.py: Handles Korean dictionary lookups
   - help.py: Provides help information
   - user.py: Manages user-related commands like /start
   - admin.py: Administrative commands for bot management

3. **keyboards/**: UI components
   - inline.py: General inline keyboard utilities
   - vocab_keyboard.py: Special keyboards for vocabulary browsing

4. **middlewares/**: Request processing middleware
   - config.py: Injects configuration into handler context

5. **filters/**: Message filtering
   - admin.py: Restricts admin commands to authorized users

6. **misc/**: Supporting utilities
   - states.py: FSM states for dialog management

7. **services/**: Additional services
   - broadcaster.py: Sends messages to multiple users

The Telegram bot module serves as the user-facing component of the application, providing an intuitive interface for interacting with the Korean Learning Bot's features.