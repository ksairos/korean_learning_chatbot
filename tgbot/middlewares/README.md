# Middleware Components Module

This module contains middleware components that process messages before they reach handlers.

## Overview

Middlewares handle cross-cutting concerns like database access and configuration management. They're applied to all messages of a specific type (e.g., messages or callback queries).

## Key Components

- **config.py**: Injects the configuration object into handler data
- **database.py**: Manages database connections and provides repositories to handlers

## Usage

Register middlewares with the dispatcher to make them active:

```python
from aiogram import Dispatcher
from tgbot.config import Config
from tgbot.middlewares.config import ConfigMiddleware

def register_middlewares(dp: Dispatcher, config: Config):
    middleware = ConfigMiddleware(config)
    
    # Apply middleware to all message handlers
    dp.message.outer_middleware(middleware)
    
    # Apply middleware to all callback query handlers
    dp.callback_query.outer_middleware(middleware)
```

Create a new middleware by extending BaseMiddleware:

```python
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

class MyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Pre-processing code here
        data["my_data"] = "some value"
        
        # Call the next middleware or handler
        result = await handler(event, data)
        
        # Post-processing code here
        
        return result
```