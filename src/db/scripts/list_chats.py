#!/usr/bin/env python
"""
A simple script to demonstrate using the synchronous database connection.
Lists all users in the database with some basic information.
"""

from contextlib import contextmanager
from src.db.database import get_sync_db

from src.db.models import ChatModel

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


def list_chats():
    """List all users in the database with some basic information."""
    with session_scope() as session:
        chats = session.query(ChatModel).all()
        
        if not chats:
            print("No chats found in the database.")
            return
        
        print(f"Total chats: {len(chats)}")
        print("-" * 60)
        
        for chat in chats:
            print(f"{chat.id:<10}")


if __name__ == "__main__":
    list_chats()