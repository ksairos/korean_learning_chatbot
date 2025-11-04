import aiohttp
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.config.settings import Config
from src.schemas.schemas import TelegramMessage, TelegramUser
from src.tgbot.misc.states import TranslationState, ConversationState
from src.tgbot.misc.utils import send_admin_message
from src.utils.json_to_telegram_md import custom_telegram_format

translation_router = Router()
config = Config()

TRANSLATION_API_URL = f"http://{config.fastapi_host}:{config.fastapi_port}/translate"


@translation_router.message(Command("translate"))
async def translate_command(message: Message, state: FSMContext):
    """Handle the /translate command"""
    await state.clear()
    await state.set_state(TranslationState.active)
    await message.answer(
        "🔄 Режим переводчика\n\n"
        "В этом режиме можешь присылать мне сообщения на русском, чтобы я перевел их на корейской и на корейском, чтобы увидеть перевод на русском\n\n"
        "Чтобы выйти: /exit"
    )


@translation_router.message(Command("exit"), TranslationState.active)
async def exit_translation_mode(message: Message, state: FSMContext):
    """Exit translation mode"""
    await state.clear()
    await message.answer("Вы вышли из режима переводчика! Чем могу помочь с грамматикой?")


@translation_router.message(TranslationState.active, F.text)
async def handle_translation_message(message: Message):
    """Handle messages in translation mode"""
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
            async with session.post(TRANSLATION_API_URL, json=telegram_message.model_dump()) as response:
                if response.status == 200:
                    result = await response.json()
                    await message.answer(custom_telegram_format(result['translation']))
                elif response.status == 403:
                    await message.answer("❌ Доступ запрещен. Обратитесь к администратору.")
                else:
                    await message.answer("⚠️ Произошла ошибка при переводе. Попробуйте позже.")

                    error_details = f"API Error {response.status}\n\nMessage: {message.text[:100]}...\n\nResponse: {response.text[:500]}..."
                    error_message = user_info + error_details
                    await send_admin_message(message.bot, error_message, "🚨 Error")
                    logging.error(f"Translation API error: {response.status}")

    except aiohttp.ClientError as e:

        await message.answer("⚠️ Не удалось подключиться к серверу. Попробуйте позже")

        error_details = f"API Error {response.status}\n\nMessage: {message.text[:100]}...\n\nResponse: {response.text[:500]}..."
        error_message = user_info + error_details
        await send_admin_message(message.bot, error_message, "🚨 Error")
        logging.error(f"Translation API connection error: {e}")

    except Exception as e:
        await message.answer("⚠️ Неизвестная ошибка. Попробуйте снова")

        error_details = f"API Error {response.status}\n\nMessage: {message.text[:100]}...\n\nResponse: {response.text[:500]}..."
        error_message = user_info + error_details
        await send_admin_message(message.bot, error_message, "🚨 Error")
        logging.error(f"Unexpected error in translation handler: {e}")