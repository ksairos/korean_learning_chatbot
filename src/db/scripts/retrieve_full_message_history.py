from contextlib import contextmanager
from sqlalchemy import desc

from rich.pretty import pprint
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from src.db.database import get_sync_db
from src.db.models import UserModel, MessageBlobModel


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

def retrieve_message_history(user_id: int) -> list[ModelMessage]:
    """
    Retrieve message history for a user, similar to get_message_history() from crud.py
    Args:
        user_id: User ID to retrieve messages for
    Returns:
        List of ModelMessage objects
    """
    with session_scope() as session:
        user = session.get(UserModel, user_id)
        chat_history: list[ModelMessage] = []
        
        if not user:
            print("User not found")
            return chat_history
            
        recent = session.execute(
            user.messages.order_by(desc(MessageBlobModel.created_at)).limit(30)
        ).scalars().all()
        
        for turn in reversed(recent):
            chat_history.extend(ModelMessagesTypeAdapter.validate_json(turn.data))
            
        # Print the parsed messages for debugging
        pprint([message.parts[0].content for message in chat_history])
        print()
        return chat_history

if __name__ == '__main__':
    retrieve_message_history(1234335061)