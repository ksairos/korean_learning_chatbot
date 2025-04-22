import logfire
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from src.db.models import ChatModel, MessageBlobModel, UserModel
from src.schemas.schemas import TelegramUser


async def add_user(session: AsyncSession, user: TelegramUser) -> None:
    """
    Add a new user to the db, if it doesn't exist already
    """
    existing_user = await session.get(UserModel, user.user_id)
    if not existing_user:
        # Add new chat
        new_chat = ChatModel(
            id=user.chat_id,
            messages=[]
        )
        # Add new user
        new_user = UserModel(
            id=user.user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            chat_id=user.chat_id,
            chat=new_chat,
        )

        session.add(new_chat)
        session.add(new_user)

        try:
            await session.commit()
            logfire.info(f"User {user.username} was added to the DB")

        except Exception as e:
            await session.rollback()
            logfire.error(f"Unexpected error: {e}")
            raise e


async def get_message_history(session: AsyncSession, user: TelegramUser, limit: int) -> list[ModelMessage]:
    """
    Get message history by using chat ID
    Args:
        session: Database session
        user: Telegram user class
        limit: Number of last turns to return
    """
    chat = await session.get(ChatModel, user.chat_id)
    chat_history: list[ModelMessage] = []

    if not chat:
        # TODO Automatically create chat when user /start
        await add_user(session, user)
        return chat_history

    recent = (
        await session.execute(
            chat.messages.
            order_by(desc(MessageBlobModel.created_at))
            .limit(limit)
        )
    ).scalars().all()

    for turn in reversed(recent):
        print(turn.created_at)
        chat_history.extend(ModelMessagesTypeAdapter.validate_json(turn.data))

    return chat_history


async def update_message_history(
    session: AsyncSession, chat_id: int, new_messages: bytes
) -> None:
    """
    Update message history by using chat ID with new messages
    Args:
        session: Database session
        chat_id: Chat ID
        new_messages: New message blobs
    """
    chat = await session.get(ChatModel, chat_id)
    if not chat:
        logfire.error(f"Something went wrong: chat {chat_id} doesn't exist")
        return

    new_message = MessageBlobModel(
        chat_id=chat_id,
        data=new_messages,
    )

    chat.messages.append(new_message)
    session.add(new_message)

    try:
        await session.commit()
        await session.refresh(new_message)

    except Exception as e:
        await session.rollback()
        logfire.error(f"An unexpected error occurred adding message to chat {chat_id}: {e}")
