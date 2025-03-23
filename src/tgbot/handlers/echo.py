from aiogram import types, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hcode
import aiohttp
import logging

echo_router = Router()

API_URL = "http://api:8000/query"

@echo_router.message(F.text, StateFilter(None))
async def bot_echo(message: types.Message):
    
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
                    llm_response = data["llm_response"]
                    
                    await message.answer(llm_response)
                    
                else:
                    logging.error(f"API error: {response.status}, {await response.text()}")
                    await message.answer("Something went wrong, please try again.")
    except Exception as e:
        logging.error(f"Error processing message via API: {e}")


@echo_router.message(F.text)
async def bot_echo_all(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    text = [
        f"Echo with state {hcode(state_name)}",
        "Message Content:",
        hcode(message.text),
    ]
    await message.answer("\n".join(text))
