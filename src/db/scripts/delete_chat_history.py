#!/usr/bin/env python
"""
Script to delete all message history for a specific chat ID.
"""

from contextlib import contextmanager
from sqlalchemy import delete

from src.db.database import get_sync_db
from src.db.models import MessageBlobModel


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_sync_db()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_chat_history(chat_id: int):
    """Delete all message history for a specific chat ID."""
    with session_scope() as session:
        # Delete all messages for the specified chat_id
        result = session.execute(
            delete(MessageBlobModel).where(MessageBlobModel.chat_id == chat_id)
        )
        deleted_count = result.rowcount
        
        print(f"Successfully deleted {deleted_count} messages for chat ID {chat_id}")


if __name__ == "__main__":
    
    delete_chat_history(1234335061)