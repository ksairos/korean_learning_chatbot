from contextlib import contextmanager
from sqlalchemy import delete

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


def delete_user(user_id: int):
    """Delete all message history for a specific chat ID."""
    with session_scope() as session:
        # Delete all messages for the specified chat_id
        session.execute(
            delete(UserModel).where(UserModel.id == user_id)
        )

        print(f"Successfully deleted user of ID {user_id}")


if __name__ == "__main__":
    delete_user(509844337)