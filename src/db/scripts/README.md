# Database Scripts

This directory contains synchronous database scripts for maintenance, reporting, and debugging purposes. These scripts use a synchronous SQLAlchemy engine instead of the async engine used by the application, making them simpler to write and run.

## Available Scripts

- **list_users.py**: Lists all users in the database with basic information
- **message_stats.py**: Shows statistics about message usage (total count, per chat, per day, per user)
- **cleanup_old_messages.py**: Utility to delete messages older than a specified time period

## Usage

To run these scripts, you need to be in the project root directory:

```bash
# List all users
python -m src.db.scripts.list_users

# View message statistics
python -m src.db.scripts.message_stats

# Clean up old messages (dry run by default)
python -m src.db.scripts.cleanup_old_messages --days 30

# Actually delete old messages
python -m src.db.scripts.cleanup_old_messages --days 30 --execute
```

## Creating New Scripts

To create a new database script:

1. Create a new Python file in this directory
2. Import the session scope context manager:
   ```python
   from contextlib import contextmanager
   from src.db.database import get_sync_db
   
   @contextmanager
   def session_scope():
       session = get_sync_db()
       try:
           yield session
           session.commit()
       except Exception:
           session.rollback()
           raise
       finally:
           session.close()
   ```

3. Use the session scope in your script:
   ```python
   with session_scope() as session:
       # Your database operations here
       result = session.query(YourModel).all()
   ```