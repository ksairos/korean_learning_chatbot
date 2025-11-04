import aiohttp
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.config.settings import Config
from src.db.crud import clear_chat_history
from src.db.database import async_session
from src.schemas.schemas import TelegramMessage, TelegramUser
from src.tgbot.misc.states import ConversationState, TranslationState
from src.tgbot.misc.utils import send_admin_message
from src.utils.json_to_telegram_md import custom_telegram_format

conversation_router = Router()
config = Config()

CONVERSATION_API_URL = f"http://{config.fastapi_host}:{config.fastapi_port}/conversation"


@conversation_router.message(Command("conversation"))
async def conversation_command(message: Message, state: FSMContext):
    """Handle the /conversation command"""
    try:
        await state.clear()
        await state.set_state(ConversationState.active)
        async with async_session() as session:
            await clear_chat_history(session, message.from_user.id)
        await message.answer(
            "🗣️ Режим разговорной практики включен\n\n"
            "Представь, что я твой корейский друг, с которым можно вести диалог 😻\n\n"
            "Можешь попросить меня исправлять ошибки или наоборот игнорировать их.\n\n"
            "- 안녕하세요?\n"
            "- 봇이라고 해요~ 반가워요!\n"
            "- 이름이 뭐예요?\n\n"
            "Чтобы выйти: /exit"
        )

    except Exception as e:
        await message.answer("Произошла ошибка, попробуйте снова")

        await send_admin_message(message.bot, e[:500], "🚨 Error")
        logging.error(f"Error clearing chat history for user {message.from_user.id}: {e}")


@conversation_router.message(Command("exit"), ConversationState.active)
async def exit_conversation_mode(message: Message, state: FSMContext):
    """Exit conversation mode"""
    await state.clear()
    try:
        async with async_session() as session:
            await clear_chat_history(session, message.from_user.id)
    except:
        pass

    await message.answer("Вы вышли из режима разговорной практики. Чем могу помочь с грамматикой?")


@conversation_router.message(ConversationState.active, F.text)
async def handle_conversation_message(message: Message):
    """Handle messages in conversation mode"""
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
            async with session.post(CONVERSATION_API_URL, json=telegram_message.model_dump()) as response:
                if response.status == 200:
                    result = await response.json()
                    await message.answer(custom_telegram_format(result['response']))
                elif response.status == 403:
                    await message.answer("❌ Доступ запрещен. Обратитесь к администратору.")
                else:
                    await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

                    error_details = f"API Error {response.status}\n\nMessage: {message.text[:100]}...\n\nResponse: {response.text[:500]}..."
                    error_message = user_info + error_details
                    await send_admin_message(message.bot, error_message, "🚨 Error")
                    logging.error(f"Conversation API error: {response.status}")

    except aiohttp.ClientError as e:
        await message.answer("⚠️ Не удалось подключиться к серверу. Попробуйте позже")

        await send_admin_message(message.bot, "Server Error", "🚨 Error")
        logging.error(f"Conversation API error: {response.status}, \n\nClientError: {e}")

    except Exception as e:

        await message.answer("⚠️ Неизвестная ошибка. Попробуйте снова")

        await send_admin_message(message.bot, "Unknown Error", "🚨 Error")
        logging.error(f"Unexpected error in conversation handler: {e}")

