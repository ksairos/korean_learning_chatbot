#!/usr/bin/env python
"""
A simple script to demonstrate using the synchronous database connection.
Lists all users in the database with some basic information.
"""

from contextlib import contextmanager
from src.db.database import get_sync_db

from src.db.models import UserModel

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


def list_users():
    """List all users in the database with some basic information."""
    with session_scope() as session:
        users = session.query(UserModel).all()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"Total users: {len(users)}")
        print("-" * 60)
        print(f"{'ID':<10} {'Username':<20} {'Full Name':<30}")
        print("-" * 60)
        
        for user in users:
            username = user.username or "N/A"
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "N/A"
            print(f"{user.id:<10} {username:<20} {full_name:<30}")


def list_user_ids():
    ids = []
    with session_scope() as session:
        users = session.query(UserModel).all()

        if not users:
            print("No users found in the database.")
            return None

        print(f"Total users: {len(users)}")

        for user in users:
            ids.append(user.id)

        return ids



if __name__ == "__main__":
    list_users()