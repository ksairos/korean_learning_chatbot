import json
from contextlib import contextmanager

from rich.pretty import pprint

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

def retrieve_message_history(user_id: int):
    with session_scope() as session:
        user = session.get(UserModel, user_id)
        if not user:
            print("User not found")
            return
        messages = user.messages
        for message in messages[:5]:
            raw_data = json.loads(message.data.decode("utf-8"))
            for item in raw_data:
                item["instructions"] = "LLM Instructions"
            pprint(raw_data, expand_all=True)

if __name__ == '__main__':
    retrieve_message_history(1234335061)