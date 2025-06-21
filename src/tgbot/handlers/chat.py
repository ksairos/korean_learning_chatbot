import asyncio

from aiogram import types, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

import aiohttp
import logging

from src.schemas.schemas import TelegramMessage, TelegramUser
from src.tgbot.misc.utils import animate_thinking

chat_router = Router()

API_URL = "http://api:8000/invoke"


@chat_router.message(F.text, StateFilter(None))
async def invoke(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        return

    try:
        thinking_message = await message.answer("•")
        animation_task = asyncio.create_task(animate_thinking(thinking_message))
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
                await thinking_message.delete()
                animation_task.cancel()
                
                if response.status == 200:
                    data = await response.json()
                    llm_response = data["llm_response"]
                    mode = data["mode"]
                    
                    logging.info(f"Message type: {type(llm_response)}\nLLM Response: {llm_response}\nMode: {mode}")
                    
                    
                    if mode == "single_grammar":
                        
                        await message.answer(llm_response[0])
                        
                    # elif mode == "multiple_grammars":
                    #     # TODO Implement multiple grammar choice
                    #     await message.answer(llm_response[0])
                    
                    # else:
                    #     # TODO Implement another answer
                    #     await message.answer("Временный ответ")

                elif response.status == 403:
                    await message.answer("Unauthorized user")

                else:
                    logging.error(
                        f"API error: {response.status}, {await response.text()}"
                    )
                    await message.answer(
                        "Произошла ошибка, сообщите в поддержку или попробуйте снова позже\n\n"
                        "Something went wrong. Report to the support or try again later.")
    except Exception as e:
        logging.error(f"Error processing message via API: {e}")
        try:
            animation_task.cancel()
            await thinking_message.delete()
        except:
            pass
