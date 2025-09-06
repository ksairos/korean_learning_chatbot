from contextlib import contextmanager
from sqlalchemy import delete

from src.config.settings import Config
from src.db.database import get_sync_db
from src.db.models import UserModel, ChatModel
from src.db.scripts.delete_user import delete_user
from src.db.scripts.list_users import list_user_ids


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


if __name__ == "__main__":
    config = Config()
    all_users = list_user_ids()

    for idx in all_users:
        if idx not in config.admin_ids:
            delete_user(idx)

