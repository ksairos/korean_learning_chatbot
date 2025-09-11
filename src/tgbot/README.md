# Telegram Bot Package

## Purpose
Modern Telegram bot frontend built with Aiogram 3.x that provides an intuitive interface for Korean language learning. Features advanced state management, interactive keyboards, and seamless integration with the multi-agent LLM backend.

## Architecture

### Bot Framework
- **Aiogram 3.x**: Modern async Telegram bot framework with FSM support
- **State Management**: Finite State Machine for complex user interactions
- **Middleware System**: Custom middleware for configuration and request processing
- **Router Pattern**: Organized handlers for different functionalities

### Integration Design
```
User → Telegram → Bot → API → LLM Agents → Vector DB
                  ↓
            Format Response → Telegram → User
```

## Core Components

### Main Application (bot.py)
- **Startup Configuration**: Bot commands, admin notifications, middleware setup
- **Storage Management**: Redis/Memory storage for FSM states
- **Polling Configuration**: Long polling with error handling
- **Middleware Registration**: Global middleware for all update types

### Handler Organization

#### Chat Handler (handlers/chat.py)
- **Message Processing**: Main text message handling and API communication
- **State Management**: Processing states to prevent message flooding
- **Grammar Selection**: Interactive grammar selection with inline keyboards
- **Response Formatting**: Converts API responses to Telegram HTML format
- **Error Handling**: Graceful handling of API failures and timeouts

#### User Handler (handlers/user.py)
- **Registration Flow**: New user onboarding and database registration
- **Profile Management**: User profile updates and settings
- **History Management**: Clear conversation history functionality
- **Authentication**: User verification and access control

#### Admin Handler (handlers/admin.py)
- **User Management**: Add/remove users from the system
- **Broadcasting**: Send messages to all users or specific groups
- **System Monitoring**: Bot status and performance metrics
- **Database Operations**: Direct database management commands

#### Help Handler (handlers/help.py)
- **Command Documentation**: Available commands and usage instructions
- **Feature Explanations**: How to use grammar search and learning features
- **Troubleshooting**: Common issues and solutions
- **Contact Information**: Support and feedback channels

#### Vocabulary Handler (handlers/vocab.py)
- **Dictionary Integration**: Korean dictionary lookup via krdict API
- **Word Search**: Korean word definitions and examples
- **Pronunciation**: Romanization and pronunciation guides
- **Learning Features**: Word saving and review functionality

### Interactive Components

#### Keyboards (keyboards/)
- **Inline Keyboards**: Grammar selection, pagination, confirmations
- **Custom Keyboards**: Quick access buttons for common functions
- **Dynamic Generation**: Context-aware keyboard layouts
- **Callback Handling**: Efficient callback query processing

#### State Management (misc/states.py)
- **Grammar Selection States**: Multi-step grammar selection flow
- **Processing States**: Prevent concurrent message processing
- **User Input States**: Capture specific user inputs
- **State Persistence**: Redis-backed state storage

### Middleware System (middlewares/)

#### Configuration Middleware
- **Settings Injection**: Provides configuration to all handlers
- **Environment Management**: Dev/prod environment handling
- **Feature Flags**: Enable/disable features per environment

#### Database Middleware (if needed)
- **Session Management**: Database session lifecycle
- **Connection Pooling**: Efficient database connections
- **Transaction Handling**: Automatic rollback on errors

### Utility Services (services/)

#### Broadcasting Service
- **Admin Notifications**: System status updates to admins
- **User Announcements**: Feature updates and maintenance notices
- **Targeted Messaging**: Send messages to specific user groups
- **Message Templates**: Reusable message formats

## Key Features

### Smart Message Processing
- **Concurrent Protection**: Prevents message flooding and race conditions
- **State-Aware Handling**: Different behavior based on user state
- **Grammar Selection Flow**: Interactive grammar selection with inline keyboards
- **Typing Animation**: Visual feedback during processing

### Response Formatting
- **Telegram HTML**: Rich text formatting for grammar explanations
- **Korean Text Support**: Proper Unicode handling for Korean characters
- **Markdown Conversion**: Converts grammar entries to readable format
- **Interactive Elements**: Buttons and keyboards for enhanced UX

### Error Handling & Resilience
- **API Timeout Handling**: Graceful handling of backend timeouts
- **Rate Limiting**: Protection against API rate limits
- **Fallback Responses**: Default responses when API unavailable
- **Error Reporting**: Automatic error logging and admin notifications

### User Experience
- **Contextual Commands**: Commands adapt to current user state
- **History Management**: Users can clear their conversation history
- **Progressive Disclosure**: Complex features revealed gradually
- **Accessibility**: Screen reader friendly text formatting

## Bot Commands

### User Commands
```
/start - Initialize bot and register user
/help - Show help and available commands  
/clear_history - Clear conversation history
/vocab <word> - Look up Korean word in dictionary
```

### Admin Commands (Admin-only)
```
/add_user <user_id> - Add user to system
/list_users - Show all registered users
/broadcast <message> - Send message to all users
/stats - Show bot usage statistics
```

## Usage Patterns

### Development
```bash
# Start bot in development
uv run python -m src.tgbot.bot

# With hot reload via Docker
docker compose up tgbot --build
```

### State Management
```python
# Set user state
await state.set_state(GrammarSelectionStates.waiting_for_selection)

# Store data in state
await state.update_data(selected_grammars=grammars)

# Retrieve state data
data = await state.get_data()
```

### Message Formatting
```python
# Format grammar for Telegram
formatted = grammar_entry_to_markdown(grammar_entry)

# Send with inline keyboard
keyboard = create_grammar_selection_keyboard(grammars)
await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
```

## Configuration
- **Bot Token**: Telegram bot token from BotFather
- **Admin IDs**: List of admin user IDs with elevated permissions
- **API Endpoints**: Backend API configuration
- **Storage**: Redis connection for state persistence
- **Webhooks**: Optional webhook configuration for production

## Error Handling Strategies
- **User-Friendly Messages**: Clear error messages in user's language
- **Automatic Retries**: Retry failed API requests with exponential backoff
- **Graceful Degradation**: Fallback responses when services unavailable
- **Admin Alerting**: Automatic notifications for critical errors

## Performance Optimizations
- **Message Batching**: Efficient handling of multiple messages
- **State Cleanup**: Automatic cleanup of expired states
- **Connection Pooling**: Reuse HTTP connections to API
- **Memory Management**: Efficient memory usage for large user bases