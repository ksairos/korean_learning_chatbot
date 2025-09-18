import logfire
from sqlalchemy import desc, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter, ModelRequest, ModelResponse

from src.db.models import MessageBlobModel, UserModel
from src.schemas.schemas import TelegramUser


async def add_user(session: AsyncSession, user: TelegramUser) -> None:
    """
    Add a new user to the db, if it doesn't exist already
    """
    existing_user = await session.get(UserModel, user.user_id)
    if not existing_user:
        # Add new user
        new_user = UserModel(
            id=user.user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            chat_id=user.chat_id,
            messages=[]
        )

        session.add(new_user)

        try:
            await session.commit()
            logfire.info(f"User {user.username} was added to the DB")

        except Exception as e:
            await session.rollback()
            logfire.error(f"Unexpected error: {e}")
            raise e


async def get_message_history(session: AsyncSession, user: TelegramUser) -> list[ModelMessage]:
    """
    Get message history by using chat ID
    Args:
        session: Database session
        user: Telegram user class
        limit: Number of last turns to return
    """
    user_model = await session.get(UserModel, user.user_id)
    chat_history: list[ModelMessage] = []

    # if not user:
    #     logfire.error(f"Chat {user.user_id} doesn't exist, adding new user")
    #     await add_user(session, user)
    #     return chat_history

    recent = (
        await session.execute(
            user_model.messages.
            where(MessageBlobModel.is_active).
            order_by(desc(MessageBlobModel.created_at)).
            limit(5)
        )
    ).scalars().all()

    for turn in reversed(recent):
        # print(turn.created_at)
        chat_history.extend(ModelMessagesTypeAdapter.validate_json(turn.data))

    return chat_history


async def update_message_history(
        session: AsyncSession,
        user: TelegramUser,
        new_messages: list[ModelRequest | ModelResponse] | bytes
) -> None:
    """
    Update message history by using chat ID with new messages
    Args:
        session: Database session
        user: Telegram user class
        new_messages: New message blobs
    """
    user_model = await session.get(UserModel, user.user_id)
    chat_history = []

    # if not user_model:
    #     logfire.error(f"Chat {user.user_id} doesn't exist, adding new user")
    #     await add_user(session, user)
    #     user_model = await session.get(UserModel, user.user_id)

    # else:
    recent = (
        await session.execute(
            user_model.messages.
            order_by(desc(MessageBlobModel.created_at))
        )
    ).scalars().all()

    for turn in reversed(recent):
        chat_history.extend(ModelMessagesTypeAdapter.validate_json(turn.data))


    # Serialize new_messages to bytes for storage
    if isinstance(new_messages, bytes):
        message_data = new_messages
    else:
        message_data = ModelMessagesTypeAdapter.dump_json(new_messages)
    
    new_message = MessageBlobModel(
        user_id=user.user_id,
        data=message_data,
    )

    user_model.messages.append(new_message)
    session.add(new_message)

    try:
        await session.commit()
        await session.refresh(new_message)

    except Exception as e:
        await session.rollback()
        logfire.error(f"An unexpected error occurred adding message to chat {user.user_id}: {e}")


async def delete_chat_history(
        session: AsyncSession,
        user: TelegramUser):
    """Delete all message history for a specific chat ID."""

    result = await session.execute(
        delete(MessageBlobModel).where(MessageBlobModel.user_id == user.user_id)
    )
    deleted_count = result.rowcount

    return deleted_count


async def clear_chat_history(session: AsyncSession, user: TelegramUser) -> int:
    """
    Mark all user's messages as inactive (soft delete for chat clearing)
    Returns the number of messages marked as inactive
    """
    result = await session.execute(
        update(MessageBlobModel)
        .where(MessageBlobModel.user_id == user.user_id)
        .values(is_active=False)
    )
    
    await session.commit()
    return result.rowcount()


async def deactivate_last_grammar_selection(session: AsyncSession, user: TelegramUser) -> bool:
    """
    Deactivate the most recent grammar selection (user selection + model response)
    Returns True if any messages were deactivated
    """
    # Find the last 2 active messages (should be selection pair)
    recent = await session.execute(
        select(MessageBlobModel)
        .where(MessageBlobModel.user_id == user.user_id)
        .where(MessageBlobModel.is_active)
        .order_by(desc(MessageBlobModel.created_at))
        .limit(1)
    )
    messages = recent.scalars().all()

    # Parse and check if it's a grammar selection
    try:
        for msg in messages:
            parsed = ModelMessagesTypeAdapter.validate_json(msg.data)
            # Check if any message contains "Selected:" indicating a grammar selection
            for message in parsed:
                if hasattr(message, 'parts'):
                    for part in message.parts:
                        if hasattr(part, 'content') and 'Selected:' in str(part.content):
                            # Mark the message as inactive
                            await session.execute(
                                update(MessageBlobModel)
                                .where(MessageBlobModel.id == msg.id)
                                .values(is_active=False)
                            )
                            await session.commit()
                            return True
    except Exception as e:
        logfire.warning(f"Error checking grammar selection messages: {e}")
    
    return False


async def get_user_ids(session: AsyncSession):
    users = await session.scalars(select(UserModel))
    ids = [row.id for row in users.all()]
    return ids


async def get_all_users(session: AsyncSession) -> list[UserModel]:
    """
    Get all users from the database with their details
    """
    result = await session.execute(select(UserModel).order_by(UserModel.created_at))
    return list(result.scalars().all())


async def delete_user_by_id(session: AsyncSession, user_id: int):
    """
    Delete a user by their ID along with all their messages
    Returns True if user was deleted, False if user not found
    """
    result = await session.execute(delete(UserModel).where(UserModel.id == user_id))
    return result.rowcount