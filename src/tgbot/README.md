# Telegram Bot Core Module

This module contains the core components for the Telegram bot implementation built using the aiogram framework.

## Overview

The `/tgbot` package serves as the main entry point for the bot's functionality and coordinates all bot-related operations.

## Key Components

- **config.py**: Configuration management for:
  - Database connections (DbConfig)
  - Telegram bot settings (TgBot)
  - Redis configuration (RedisConfig)
  - Miscellaneous settings

## Usage

Configuration is loaded from environment variables:

```python
from src.config import load_config

config = load_config(".env")
```

The bot supports both database and Redis integrations. The configuration is centralized and injected into various components through middleware.