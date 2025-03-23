# Message Filters Module

This module provides custom filters to control message processing flow in the bot.

## Overview

Filters determine whether a particular handler should process an incoming message or callback. They help route messages to the appropriate handlers based on criteria such as user role, message content, or chat type.

## Key Components

- **admin.py**: Defines the `AdminFilter` class that filters messages based on whether they come from admin users.

## Usage

Attach filters to handlers to enable conditional processing:

```python
from aiogram import Router
from src.tgbot.filters.admin import AdminFilter

router = Router()


@router.message(AdminFilter())
async def admin_command_handler(message: Message):
    # This handler only processes messages from admins
    await message.answer("Hello, admin!")
```

Filters can be combined using logical operators for complex conditions.