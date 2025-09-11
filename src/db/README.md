# Database Package

## Purpose
Handles all database operations for the Korean learning chatbot, including user management, conversation history tracking, and message storage. Built on PostgreSQL with async SQLAlchemy ORM for high-performance concurrent operations.

## Architecture

### Database Schema Design
- **UserModel**: Core user registry with Telegram BigInteger IDs
- **MessageBlobModel**: Conversation history stored as binary Pydantic AI message blobs
- **Soft Delete Pattern**: Messages marked inactive rather than deleted (is_active flag)
- **UUID Primary Keys**: Message blobs use UUIDs for distributed-friendly IDs

### Key Design Decisions
- **Binary Message Storage**: Pydantic AI messages serialized as binary blobs for flexibility
- **User-Centric Design**: All operations keyed by Telegram user ID
- **Async-First**: All database operations are async for scalability
- **Migration Support**: Full Alembic integration for schema evolution

## Key Components

### Core Files
- **models.py**: SQLAlchemy models with proper relationships and constraints
- **crud.py**: Async CRUD operations with comprehensive error handling
- **database.py**: Database session management and dependency injection
- **scripts/**: Utility scripts for maintenance and debugging

### Database Models

#### UserModel
```python
class UserModel(Base):
    id: BigInteger (Primary Key)          # Telegram user ID
    username: str (Optional)              # Telegram username
    first_name: str                       # User's first name
    last_name: str (Optional)             # User's last name
    chat_id: BigInteger (Unique)          # Telegram chat ID
    created_at: DateTime                  # Registration timestamp
    messages: relationship -> MessageBlobModel
```

#### MessageBlobModel
```python
class MessageBlobModel(Base):
    id: UUID (Primary Key)                # Unique message identifier
    user_id: BigInteger (Foreign Key)     # Reference to user
    data: LargeBinary                     # Serialized Pydantic AI messages
    is_active: Boolean                    # Soft delete flag
    created_at: DateTime                  # Message timestamp
    user: relationship -> UserModel
```

## Key Functions

### User Management
- **`add_user(session, user)`**: Register new Telegram user with error handling
- **`get_user_ids(session)`**: Retrieve all registered user IDs for authentication
- **`get_user_by_id(session, user_id)`**: Fetch user details by Telegram ID

### Message History
- **`get_message_history(session, user)`**: Retrieve conversation history as Pydantic AI messages
- **`update_message_history(session, user, messages)`**: Store new conversation turns
- **`clear_user_history(session, user_id)`**: Soft delete all user messages
- **`get_message_stats(session)`**: Retrieve usage statistics

### Binary Message Handling
- **Serialization**: Pydantic AI messages → binary blob storage
- **Deserialization**: Binary blob → typed Pydantic AI message objects
- **Error Recovery**: Graceful handling of corrupt message data

## Database Operations

### Migrations
```bash
# Apply pending migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check current revision
alembic current

# View migration history
alembic history
```

### Connection Management
```python
# Database URL construction from config
asyncpg_url = MultiHostUrl.build(
    scheme="postgresql+asyncpg",
    username=postgres_user,
    password=postgres_password,
    host=postgres_host,
    port=postgres_port,
    path=postgres_db,
)
```

## Utility Scripts (scripts/)

### User Management
- **`list_users.py`**: Display all registered users
- **`delete_user.py`**: Remove user and all associated data
- **`delete_non_admins.py`**: Clean up non-admin users

### Message Management
- **`delete_chat_history.py`**: Clear conversation history for users
- **`retrieve_message_history.py`**: Export user conversations
- **`message_stats.py`**: Generate usage analytics

### Usage Examples
```bash
# List all users
python -m src.db.scripts.list_users

# Clear user history
python -m src.db.scripts.delete_chat_history --user_id 123456789

# Get message statistics
python -m src.db.scripts.message_stats
```

## Dependencies
- **PostgreSQL 15+**: Primary database engine
- **SQLAlchemy 2.0**: Async ORM with modern API
- **Asyncpg**: High-performance PostgreSQL driver
- **Alembic**: Database migration management
- **Pydantic**: Message validation and serialization
- **Logfire**: Database operation logging and monitoring

## Configuration
Database settings managed through `src/config/settings.py`:
- **Connection pooling**: Automatic pool management
- **SSL support**: Production-ready security
- **Connection retries**: Robust error handling
- **Logging integration**: Comprehensive operation tracking

## Performance Considerations
- **Async Operations**: Non-blocking database access
- **Connection Pooling**: Efficient resource utilization  
- **Indexed Queries**: Optimized query performance
- **Binary Storage**: Compact message representation
- **Soft Deletes**: Fast "deletion" without data loss