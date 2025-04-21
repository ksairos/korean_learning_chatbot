from aiogram import types, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from chatgpt_md_converter import telegram_format

import aiohttp
import logging

from src.schemas.schemas import TelegramMessage, TelegramUser

chat_router = Router()

API_URL = "http://api:8000/invoke"


@chat_router.message(F.text, StateFilter(None))
async def invoke(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        return

    try:
        async with aiohttp.ClientSession() as session:
            user = TelegramUser(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                chat_id=message.chat.id
            )
            telegram_message = TelegramMessage(
                user_prompt=message.text,
                user=user
            )
            async with session.post(
                API_URL, json=telegram_message.model_dump()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    llm_response = data["llm_response"]
                    # mode = data["mode"]

                    formatted_response = telegram_format(llm_response)

                    await message.answer(formatted_response)

                else:
                    logging.error(
                        f"API error: {response.status}, {await response.text()}"
                    )
                    await message.answer("Something went wrong, please try again.")
    except Exception as e:
        logging.error(f"Error processing message via API: {e}")
