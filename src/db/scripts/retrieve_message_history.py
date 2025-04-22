import json
from contextlib import contextmanager

from rich.pretty import pprint

from src.db.database import get_sync_db

from src.db.models import UserModel, ChatModel, MessageBlobModel


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

def retrieve_message_history(chat_id: int):
    with session_scope() as session:
        chat = session.get(ChatModel, chat_id)
        if not chat:
            print("Chat not found")
            return
        messages = chat.messages
        for message in messages[:5]:
            raw_data = json.loads(message.data.decode("utf-8"))
            for item in raw_data:
                item["instructions"] = "LLM Instructions"
            pprint(raw_data, expand_all=True)




if __name__ == '__main__':
    retrieve_message_history(1234335061)