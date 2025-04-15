from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ChatModel


async def get_message_history(db: AsyncSession, chat_id: int, user_id: int, ):
    """
    Get message history by using chat ID
    Args:
        db: Database session
        chat_id: Chat ID
        user_id: User ID
    """
    stmt = (select(ChatModel).where(ChatModel.chat_id == chat_id))
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()

    if not chat:
        # TODO Automatically create chat when user /start
        chat = ChatModel(
            chat_id=chat_id,
            user_id=user_id
        )
        db.add(chat)
        await db.commit()

    return chat


async def update_message_history(db: AsyncSession, chat_id: int, role: str, content: str) -> None:
    """
    Update message history by using chat ID with new messages
    Args:
        db:
        chat_id:
        role:
        content:
    """
    pass