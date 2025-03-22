# Keyboard Builders Module

This module contains keyboard builders for creating interactive interfaces in the bot.

## Overview

Telegram bots can display custom keyboards to users for easier interaction. This module provides builders for both inline keyboards (appearing under messages) and reply keyboards (replacing the standard keyboard).

## Key Components

- **inline.py**: Implements inline keyboard builders with:
  - Simple callback buttons
  - CallbackData factory for structured data in callbacks
  - Dynamic keyboard generation from data

- **reply.py**: Provides reply keyboard implementations

## Usage

### Inline Keyboards

```python
from tgbot.keyboards.inline import make_callback_data, make_inline_keyboard

# Using a CallbackData factory for type-safe callbacks
callback_data = make_callback_data("action", "item_id")
keyboard = make_inline_keyboard(
  [
    [{"text": "Option 1", "callback_data": callback_data.new(action="select", item_id="1")}],
    [{"text": "Option 2", "callback_data": callback_data.new(action="select", item_id="2")}]
  ]
)

await message.answer("Choose an option:", reply_markup=keyboard)
```

### Reply Keyboards

```python
from tgbot.keyboards.reply import make_reply_keyboard

keyboard = make_reply_keyboard(
  [["Option 1", "Option 2"],
   ["Option 3", "Option 4"]]
)

await message.answer("Choose an option:", reply_markup=keyboard)
```