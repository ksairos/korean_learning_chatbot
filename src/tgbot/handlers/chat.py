from aiogram import types, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from chatgpt_md_converter import telegram_format

import aiohttp
import logging

from src.tgbot.handlers.vocab import start_vocab_mode

chat_router = Router()

API_URL = "http://api:8000/invoke"

@chat_router.message(F.text, StateFilter(None))
async def invoke(message: types.Message, state: FSMContext):
    
    if message.text.startswith('/'):
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                json={"user_prompt": message.text}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    llm_response = data["response"]

                    formatted_response = telegram_format(llm_response)
                    
                    await message.answer(formatted_response)
                    
                    # TODO можно попробовать тут триггерить режимы, в зависимости от ответа 
                    # await start_vocab_mode(state, message.answer)
                    
                else:
                    logging.error(f"API error: {response.status}, {await response.text()}")
                    await message.answer("Something went wrong, please try again.")
    except Exception as e:
        logging.error(f"Error processing message via API: {e}")