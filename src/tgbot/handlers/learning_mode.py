import aiohttp
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import numpy as np
from qdrant_client import AsyncQdrantClient

from src.config.settings import Config
from src.db.crud import clear_chat_history
from src.db.database import async_session
from src.schemas.schemas import TelegramMessage, TelegramUser, GrammarEntryV2
from src.tgbot.misc.states import LearningState
from src.tgbot.misc.utils import send_admin_message
from src.utils.json_to_telegram_md import custom_telegram_format
from src.utils.old.json_to_telegram_md_old import grammar_entry_to_markdown

learning_router = Router()
config = Config()

client = AsyncQdrantClient(host=config.qdrant_host, port=config.qdrant_port)
collection_name = config.qdrant_collection_name_final

LEARNING_API_URL = f"http://{config.fastapi_host}:{config.fastapi_port}/learning"

async def get_random_grammar():
    collection_info = await client.get_collection(collection_name)
    vector_size = collection_info.config.params.vectors.size
    random_vector = np.random.uniform(-1, 1, size=vector_size).tolist()
    results = await client.query_points(
        collection_name=collection_name,
        query=random_vector,
        limit=1,
        with_payload=True
    )
    if results.points:
        hit = results.points[0]
        content = GrammarEntryV2(**hit.payload)
        return content
    else:
        return None


@learning_router.message(Command("learning"))
async def learning_command(message: Message, state: FSMContext):
    """Handle the /learning command"""
    try:
        await state.clear()
        await state.set_state(LearningState.active)
        await state.update_data(turn_count=0)
        async with async_session() as session:
            await clear_chat_history(session, message.from_user.id)

        await message.answer(
            "🗣️Режим изучения грамматики включен\n\n"
            "Чтобы выйти: /exit"
        )

        grammar = await get_random_grammar()

    except Exception as e:
        await message.answer("Произошла ошибка, попробуйте снова")

        await send_admin_message(message.bot, e[:500], "🚨 Error")
        logging.error(f"Error clearing chat history for user {message.from_user.id}: {e}")

@learning_router.message(Command("exit"), LearningState.active)
async def exit_learning_mode(message: Message, state: FSMContext):
    """Exit learning mode"""
    await state.clear()
    try:
        async with async_session() as session:
            await clear_chat_history(session, message.from_user.id)
    except:
        pass

    await message.answer("Вы вышли из режима изучения с практикой. Чем я могу помочь с грамматикой?")


@learning_router.message(LearningState.active, F.text)
async def handle_learning_message(message: Message):
    """Handle messages in learning mode"""
    if message.text.startswith("/"):
        return

    telegram_user = TelegramUser(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
        chat_id=message.from_user.id
    )

    telegram_message = TelegramMessage(
        user=telegram_user,
        user_prompt=message.text
    )

    user_info = f"@{message.from_user.username or 'N/A'} (ID: {message.from_user.id})\n\n"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                LEARNING_API_URL, json=telegram_message.model_dump()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    await message.answer(custom_telegram_format(result["response"]))

                elif response.status == 403:
                    await message.answer(
                        "❌ Доступ запрещен. Обратитесь к администратору."
                    )
                else:
                    await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

                    error_details = f"API Error {response.status}\n\nMessage: {message.text[:100]}...\n\nResponse: {response.text[:500]}..."
                    error_message = user_info + error_details
                    await send_admin_message(message.bot, error_message, "🚨 Error")
                    logging.error(f"Conversation API error: {response.status}")

    except aiohttp.ClientError as e:
        await message.answer("⚠️ Не удалось подключиться к серверу. Попробуйте позже")

        await send_admin_message(message.bot, "Server Error", "🚨 Error")
        logging.error(
            f"Conversation API error: {response.status}, \n\nClientError: {e}"
        )

    except Exception as e:
        await message.answer("⚠️ Неизвестная ошибка. Попробуйте снова")

        await send_admin_message(message.bot, "Unknown Error", "🚨 Error")
        logging.error(f"Unexpected error in conversation handler: {e}")
