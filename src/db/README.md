# Database Package

## Purpose
Provides database operations and models for the Korean learning chatbot. Handles user management, chat history, and message storage using PostgreSQL with SQLAlchemy ORM.

## Key Components
- **models.py**: SQLAlchemy models for users, chats, and message history
- **crud.py**: CRUD operations for user management and message history
- **database.py**: Database session management and connection setup
- **scripts/**: Database utility scripts for chat management and statistics

## Models
- **UserModel**: User information (ID, username, first name, last name, chat reference)
- **ChatModel**: Chat sessions with message history
- **MessageBlobModel**: Individual message storage with timestamps

## Dependencies
- **src/schemas/**: Pydantic models for data validation
- **src/config/**: Database configuration settings

## Key Functions
- `add_user()`: Creates new user and associated chat
- `get_message_history()`: Retrieves conversation history for a user
- `update_message_history()`: Stores new messages in database
- `get_user_ids()`: Returns list of registered user IDs

## Database Operations
Run migrations:
```bash
alembic upgrade head
```

Create migration:
```bash
alembic revision --autogenerate -m "message"
```

## Connection
The package connects to PostgreSQL database using async SQLAlchemy sessions managed through dependency injection in the API layer.