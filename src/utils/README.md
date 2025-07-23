# Utils Package

## Purpose
Provides utility functions for text processing, data formatting, and content transformation used throughout the Korean learning chatbot system.

## Key Components
- **json_to_telegram_md.py**: Converts JSON grammar entries to Telegram-compatible HTML format
- **md_to_json.py**: Processes markdown files and converts them to JSON format
- **parse_entry_for_embedding.py**: Prepares text entries for vector embedding generation
- **strip_markdown.py**: Removes markdown formatting from text
- **old/**: Legacy utility functions preserved for reference

## Key Functions
- `custom_telegram_format()`: Converts markdown to Telegram HTML with proper escaping
- `grammar_entry_to_markdown()`: Formats grammar entries for display in Telegram
- `split_by_tag()`: Handles markdown tag conversion to HTML
- `extract_inline_code_snippets()`: Preserves code formatting during conversion

## Dependencies
- **chatgpt_md_converter**: Third-party library for markdown processing
- **src/schemas/**: Data models for grammar entries

## Usage
Primary use cases:
- Converting LLM responses to Telegram-compatible format
- Processing grammar database entries for display
- Preparing text for vector embedding operations
- Cleaning and formatting user input

## Integration
- **src/tgbot/**: Uses formatting functions for message display
- **src/llm_agent/**: Processes responses before returning to bot
- **notebooks/**: Data preprocessing and transformation scripts

## Text Processing Features
- HTML entity escaping for Telegram
- Markdown to HTML conversion
- Code block preservation
- Link and image formatting
- Unicode handling for Korean text