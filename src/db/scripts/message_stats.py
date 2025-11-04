#!/usr/bin/env python
"""
A script to display statistics about messages in the database.
Uses the synchronous database connection for direct DB access.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta

from src.db.database import get_sync_db
from src.db.models import MessageBlobModel, UserModel
from sqlalchemy import func


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


def get_message_statistics():
    """Get statistics about messages in the database."""
    with session_scope() as session:
        # Get total message count
        total_messages = session.query(func.count(MessageBlobModel.id)).scalar() or 0
        
        if total_messages == 0:
            print("No messages found in the database.")
            return
        
        # Get message count per chat
        chat_message_counts = (
            session.query(
                UserModel.id,
                func.count(MessageBlobModel.id).label('message_count')
            )
            .join(MessageBlobModel, MessageBlobModel.user_id == UserModel.id)
            .group_by(UserModel.id)
            .all()
        )
        
        # Get message count by day for the last 7 days
        one_week_ago = datetime.now() - timedelta(days=7)
        daily_counts = (
            session.query(
                func.date_trunc('day', MessageBlobModel.created_at).label('day'),
                func.count(MessageBlobModel.id).label('count')
            )
            .filter(MessageBlobModel.created_at >= one_week_ago)
            .group_by('day')
            .order_by('day')
            .all()
        )
        
        # Get most active users
        most_active_users = (
            session.query(
                UserModel.id,
                UserModel.username,
                UserModel.first_name,
                func.count(MessageBlobModel.id).label('message_count')
            )
            .join(UserModel, UserModel.id == UserModel.id)
            .join(MessageBlobModel, MessageBlobModel.user_id == UserModel.id)
            .group_by(UserModel.id)
            .order_by(func.count(MessageBlobModel.id).desc())
            .limit(5)
            .all()
        )
        
        # Display statistics
        print(f"Total messages: {total_messages}")
        print("\nMessage count per chat:")
        for chat_id, count in chat_message_counts:
            print(f"  Chat ID {chat_id}: {count} messages")
        
        print("\nMessages per day (last 7 days):")
        for day, count in daily_counts:
            print(f"  {day.strftime('%Y-%m-%d')}: {count} messages")
        
        print("\nMost active users:")
        for user_id, username, first_name, count in most_active_users:
            display_name = username or first_name or f"User {user_id}"
            print(f"  {display_name}: {count} messages")


if __name__ == "__main__":
    get_message_statistics()