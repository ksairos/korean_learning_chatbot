# Message Handlers Module

This module contains message handlers that process user interactions with the bot.

## Overview

Handlers define the bot's responses to commands, messages, and callback queries. They're organized by functionality and user type to maintain a clean separation of concerns.

## Key Components

- **admin.py**: Handles admin-specific commands and interactions
- **echo.py**: Implements echo functionality (repeating back user messages)
- **simple_menu.py**: Implements menu navigation using inline keyboards and callback queries
- **user.py**: Manages regular user interactions, including the start command

## Usage

New handlers should be organized by function and user type:

1. Create a new handler file in this directory
2. Define a router and attach handlers to it:
   ```python
   from aiogram import Router, F
   from aiogram.types import Message
   
   my_router = Router()
   
   @my_router.message(commands=["mycommand"])
   async def my_command(message: Message):
       await message.answer("Command received!")
   ```
3. Register your router in `__init__.py` by adding it to `routers_list`

The order of routers in `routers_list` matters. More specific handlers should come first, with the echo handler always last as a fallback.