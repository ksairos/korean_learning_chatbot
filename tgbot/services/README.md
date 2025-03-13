# Service Utilities Module

This module provides utility services that support the bot's functionality.

## Overview

Services provide functionality that doesn't fit into handlers or middlewares. They typically handle operations that are used across multiple handlers or require specialized error handling.

## Key Components

- **broadcaster.py**: Implements safe message broadcasting to multiple users with:
  - Rate limiting to avoid flood limits
  - Error handling and logging
  - Recursive retry logic for temporary failures

## Usage

### Broadcasting Messages

```python
from aiogram import Bot
from tgbot.services.broadcaster import broadcast

async def notify_admins(bot: Bot, admin_ids: list[int], message: str):
    # Safely send a message to all admins
    await broadcast(bot, admin_ids, message)
```

### Adding New Services

New services should be added to this module when they:
- Provide functionality used by multiple handlers
- Require specialized error handling
- Handle complex bot operations
- Interact with external systems

Services should be stateless when possible to facilitate testing and reliability.