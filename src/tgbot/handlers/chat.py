import asyncio
from datetime import datetime, timedelta

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import aiohttp
import logging

from src.config.settings import Config
from src.schemas.schemas import TelegramMessage, TelegramUser
from src.tgbot.misc.utils import animate_thinking
from src.utils.json_to_telegram_md import grammar_entry_to_markdown, custom_telegram_format

chat_router = Router()
config = Config()

API_URL = f"http://{config.fastapi_host}:{config.fastapi_port}/invoke"


class GrammarSelectionStates(StatesGroup):
    waiting_for_selection = State()


@chat_router.message(F.text)
async def invoke(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        return
    
    # Clear any existing state when user sends new message
    current_state = await state.get_state()
    if current_state:
        await state.clear()

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
                    
                    # logging.info(f"\n================\nMessage type: {type(llm_response)}\nLLM Response: {llm_response}\nMode: {mode}\n================\n")

                    # INFO: Handle different modes (by number of grammars found)

                    if mode == "single_grammar":
                        formatted_response = grammar_entry_to_markdown(llm_response[0])
                        await message.answer(formatted_response)

                    elif mode == "multiple_grammars":
                        await state.set_state(GrammarSelectionStates.waiting_for_selection)
                        await state.update_data(
                            grammars=llm_response,
                            selection_timestamp=datetime.now().isoformat()
                        )

                        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                        for i, grammar in enumerate(llm_response):
                            # Truncate title if too long for button
                            grammar_name_kr = grammar["grammar_name_kr"].strip()
                            grammar_name_rus = grammar["grammar_name_rus"].strip()
                            title = f"{grammar_name_kr} - {grammar_name_rus}"[:50]
                            if not title:
                                title = f"Грамматика {i}"

                            button = InlineKeyboardButton(
                                text=title,
                                callback_data=f"grammar_select:{i}"
                            )
                            keyboard.inline_keyboard.append([button])

                        prompt_text = f"Грамматик по вашему запросу: {len(llm_response)}. Выберите одну:"
                        await message.answer(prompt_text, reply_markup=keyboard)


                    elif mode == "no_grammars":
                        # FIXME Implement another answer
                        await message.answer("К сожалению, я не смог найти подходящие грамматики в своей базе. Однако я могу попробовать ответить сам ☝️🤓")
                        await message.answer(custom_telegram_format(llm_response))

                    else:
                        await message.answer(custom_telegram_format(llm_response))

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


@chat_router.callback_query(F.data.startswith("grammar_select:"))
async def handle_grammar_selection(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Extract grammar index from callback data
        grammar_index = int(callback.data.split(":")[1])

        # Get stored grammar data
        data = await state.get_data()
        grammars = data.get("grammars", [])
        timestamp_str = data.get("selection_timestamp")
        
        # Check if selection has expired (10 minutes)
        if timestamp_str:
            selection_time = datetime.fromisoformat(timestamp_str)
            if datetime.now() - selection_time > timedelta(minutes=10):
                await callback.answer("Selection expired. Please search again.", show_alert=True)
                await state.clear()
                return

        if 0 <= grammar_index < len(grammars):
            selected_grammar = grammars[grammar_index]
            formatted_response = grammar_entry_to_markdown(selected_grammar)
            
            # Check if this user already has a response message
            response_message_id = data.get("response_message_id")
            
            if response_message_id:
                # Edit the existing response message
                try:
                    await callback.bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=response_message_id,
                        text=formatted_response
                    )
                except Exception as e:
                    # If editing fails, send new message
                    logging.warning(f"Failed to edit message {response_message_id}: {e}")
                    response_msg = await callback.message.answer(formatted_response)
                    await state.update_data(response_message_id=response_msg.message_id)
            else:
                # Send new response message and store its ID
                response_msg = await callback.message.answer(formatted_response)
                await state.update_data(response_message_id=response_msg.message_id)
        else:
            await callback.answer("Invalid selection", show_alert=True)

    except (ValueError, IndexError) as e:
        logging.error(f"Error processing grammar selection: {e}")
        await callback.answer("Error processing selection", show_alert=True)

    finally:
        # Don't clear state - keep it for multiple selections
        await callback.answer()
