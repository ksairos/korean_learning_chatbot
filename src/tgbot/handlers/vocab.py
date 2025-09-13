# from typing import Callable, Optional
#
# import krdict
# import re
#
# from aiogram import Router, F
# from aiogram.filters import StateFilter, Command
# from aiogram.fsm.context import FSMContext
# from aiogram.types import CallbackQuery, ReplyKeyboardRemove, Message
#
# from src.config.settings import Config
# from src.tgbot.keyboards.vocab_keyboard import word_keyboard, examples_keyboard, exit_keyboard
# from src.tgbot.misc.states import VocabState
#
# config = Config()
# krdict.set_key(config.krdict_api_key)
#
# dictionary_router = Router()
#
# def format_dictionary_response_custom(response):
#     pos_mapping = {
#         "전체": "Общее",
#         "명사": "Существительное",
#         "대명사": "Местоимение",
#         "수사": "Числительное",
#         "조사": "Послелог",
#         "동사": "Глагол",
#         "형용사": "Прилагательное",
#         "관형사": "Атрибутив",
#         "부사": "Наречие",
#         "감탄사": "Междометие",
#         "접사": "Аффикс",
#         "의존 명사": "Зависимое существительное",
#         "보조 동사": "Вспомогательный глагол",
#         "보조 형용사": "Вспомогательное прилагательное",
#         "어미": "Финальное окончание",
#         "품사 없음": "Без категории"
#     }
#     difficulty_mapping = {
#         "초급": "(⭐)",
#         "중급": "(⭐⭐)",
#         "고급": "(⭐⭐⭐)",
#         "": "🤷‍️"
#     }
#
#     results = response.get("data", {}).get("results", [])
#     formatted_results = []
#
#     for res in results:
#         # Extract header information.
#         word = res.get("word", "")
#         vocabulary_level = res.get("vocabulary_level", "")
#         vocabulary_level_emoji = difficulty_mapping.get(vocabulary_level, "")
#         url = re.sub(r'/kor/', '/rus/', res.get("url", ""))
#         pos = res.get("part_of_speech", "")
#         pos_russian = pos_mapping.get(pos, pos)
#
#         # Format header: first line Korean word, second line Russian pos and Korean pos in parentheses.
#         header = (f"📚 <b><a href='{url}'>{word}</a></b>\n"
#                   f"{pos_russian} ({pos})\n"
#                   f"Уровень: {vocabulary_level}{vocabulary_level_emoji}")
#
#         # Process each definition.
#         definitions_str = ""
#         for definition in res.get("definitions", []):
#             order = definition.get("order", "")
#             korean_def = definition.get("definition", "")
#             translations = definition.get("translations", [])
#
#             # Use the first translation if available.
#             if translations:
#                 first_trans = translations[0]
#                 trans_word = first_trans.get("word", "").strip()
#                 # If translation word is missing, use the fallback.
#                 if not trans_word:
#                     trans_word = "<s>нет эквивалента</s>"
#                 trans_def = first_trans.get("definition", "").strip()
#             else:
#                 trans_word = "<s>нет эквивалента</s>"
#                 trans_def = ""
#
#             # Build the formatted definition:
#             #  - A line with the order number and the underlined translated word.
#             #  - A blockquote that shows the Korean definition followed by the Russian explanation.
#             definitions_str += f"\n\n{order}. <b>{trans_word}</b>\n"
#             definitions_str += "<blockquote>"
#             if trans_def:
#                 definitions_str += f"{trans_def}\n\n"
#             definitions_str += f"{korean_def}\n"
#             definitions_str += "</blockquote>"
#
#         formatted_result = header + definitions_str
#         formatted_results.append(formatted_result)
#
#     return formatted_results
#
#
# def format_examples(response, page=0, per_page=5, original_word=None):
#     """
#     Format examples from the API response with pagination.
#
#     Args:
#         response: The API response dictionary
#         page: The page number (0-based)
#         per_page: Number of examples per page
#         original_word: The original word the examples are for
#
#     Returns:
#         A formatted string with multiple examples and pagination info
#     """
#     results = response.get("data", {}).get("results", [])
#     total_results = len(results)
#     total_pages = (total_results + per_page - 1) // per_page  # Ceiling division
#
#     if not results:
#         if original_word:
#             return f"Примеры для слова <b>{original_word}</b> не найдены."
#         else:
#             return "Примеры не найдены."
#
#     # Calculate start and end indices for current page
#     start_idx = page * per_page
#     end_idx = min(start_idx + per_page, total_results)
#
#     # Create header with the original word and pagination info
#     if original_word:
#         header = f"<b>📚 {original_word}</b>\n"
#         header += f"<b>Примеры {start_idx + 1}-{end_idx}/{total_results}</b> (Страница {page + 1}/{total_pages})\n\n"
#     else:
#         header = f"<b>Примеры {start_idx + 1}-{end_idx}/{total_results}</b> (Страница {page + 1}/{total_pages})\n\n"
#
#     examples_text = []
#
#     # Format each example in the current page
#     for i, result in enumerate(results[start_idx:end_idx], start_idx + 1):
#         word = result.get("word", "")
#         example = result.get("example", "")
#         url = result.get("url", "")
#
#         example_text = (
#             f"{i}. {example} (лексика: <a href='{url}'>{word}</a>)\n"
#         )
#         examples_text.append(example_text)
#
#     # Join all examples with a separator
#     formatted_output = header + "\n".join(examples_text)
#
#     return formatted_output
#
#
# async def start_vocab_mode(state: FSMContext, answer_function: Callable):
#     """Handler for /vocab command to enter the dictionary mode"""
#     # Set the state to active vocabulary mode
#     await state.set_state(VocabState.active)
#
#     await answer_function(
#         "🔍 Вы вошли в режим корейско-русского словаря. Отправьте КОРЕЙСКОЕ слово, чтобы получить его определение из официального Словаря Национального Института Корейского Языка (한국어기초사전).\n\n"
#         "Чтобы выйти из режима словаря, нажмите кнопку 'Выйти из словаря 🚪' или отправьте команду /exit."
#     )
#
# # Command to enter the dictionary mode through button (callback)
# @dictionary_router.callback_query(F.data == "vocab")
# async def start_vocab_mode_callback(query: CallbackQuery, state: FSMContext):
#     await query.answer()
#     await start_vocab_mode(state, query.message.answer)
#
# # Command to enter the dictionary mode through /vocab
# @dictionary_router.message(Command("vocab"))
# async def start_vocab_mode_message(message: Message, state: FSMContext):
#     await start_vocab_mode(state, message.answer)
#
# # Handler for exiting vocab mode via command
# @dictionary_router.message(Command("exit"), StateFilter(VocabState.active))
# async def exit_vocab_mode_command(message: Message, state: FSMContext):
#     """Handler to exit the dictionary mode using command"""
#     await state.clear()
#     await message.answer(
#         "Вы вышли из режима словаря.",
#         reply_markup=ReplyKeyboardRemove()
#     )
#
# # Handler for text messages when in vocab mode
# @dictionary_router.message(F.text, StateFilter(VocabState.active))
# async def dictionary_bot(message: Message, state: FSMContext, query: Optional[str] = None):
#     """Handler for dictionary queries when in vocab mode"""
#
#     if not query:
#         query = message.text
#
#     response = krdict.search(
#         search_type=krdict.SearchType.WORD,
#         query=query,
#         raise_api_errors=True,
#         translation_language='russian',
#         per_page=10
#     ).asdict()
#
#     # Get the formatted list
#     formatted_list = format_dictionary_response_custom(response)
#
#     # Store the formatted results, raw response, and current index in state
#     await state.update_data(
#         search_results=response,
#         formatted_results=formatted_list,
#         current_index=0,
#         total_results=len(formatted_list)
#     )
#
#     try:
#         answer = formatted_list[0]
#         await message.answer(answer, reply_markup=word_keyboard())
#
#     except IndexError:
#         await message.answer(
#             "Ничего не найдено. Попробуйте другое слово или нажмите кнопку ниже для выхода из режима словаря.",
#             reply_markup=exit_keyboard()
#         )
#
# # Handle next_word button callback
# @dictionary_router.callback_query(F.data == "next_word")
# async def next_word(query: CallbackQuery, state: FSMContext):
#     # Always answer callback query first (as Telegram API requires)
#     await query.answer()
#
#     # Get current data from state
#     data = await state.get_data()
#     current_index = data.get("current_index", 0)
#     formatted_results = data.get("formatted_results", [])
#     total_results = data.get("total_results", 0)
#
#     # Calculate next index (with wraparound)
#     next_index = current_index + 1
#     if next_index >= total_results:
#         next_index = 0
#
#     # Update state with new index
#     await state.update_data(current_index=next_index)
#
#     # Show the next word
#     if formatted_results and next_index < len(formatted_results):
#         await query.message.edit_text(
#             formatted_results[next_index],
#             reply_markup=word_keyboard()
#         )
#     else:
#         await query.message.answer("No more words available.")
#
# # Handle previous_word button callback
# @dictionary_router.callback_query(F.data == "previous_word")
# async def show_previous_word(query: CallbackQuery, state: FSMContext):
#     await query.answer()
#
#     # Get current data from state
#     data = await state.get_data()
#     current_index = data.get("current_index", 0)
#     formatted_results = data.get("formatted_results", [])
#     total_results = data.get("total_results", 0)
#
#     # Calculate previous index (with wraparound)
#     prev_index = current_index - 1
#     if prev_index < 0:
#         prev_index = total_results - 1 if total_results > 0 else 0
#
#     # Update state with new index
#     await state.update_data(current_index=prev_index)
#
#     # Show the previous word
#     if formatted_results and 0 <= prev_index < len(formatted_results):
#         await query.message.edit_text(
#             formatted_results[prev_index],
#             reply_markup=word_keyboard()
#         )
#     else:
#         await query.message.answer("No previous words available.")
#
# # Handle show_examples button callback
# @dictionary_router.callback_query(F.data == "show_examples")
# async def show_examples(query: CallbackQuery, state: FSMContext):
#     """Handle show examples button press by fetching examples from the API."""
#     await query.answer()
#
#     # Get current data from state
#     data = await state.get_data()
#     current_index = data.get("current_index", 0)
#     search_results = data.get("search_results", {})
#
#     # Get the current word data
#     results = search_results.get("data", {}).get("results", [])
#
#     if results and 0 <= current_index < len(results):
#         word_data = results[current_index]
#         word = word_data.get("word", "")
#
#         try:
#             # Make API call to get examples for this word - Get more examples per page
#             examples_response = krdict.search(
#                 search_type=krdict.SearchType.EXAMPLE,
#                 query=word,
#                 translation_language='russian',
#                 raise_api_errors=True,
#                 per_page=100  # Fetch more examples at once
#             ).asdict()
#
#             # Get total examples count and calculate total pages
#             total_results = len(examples_response.get("data", {}).get("results", []))
#             per_page = 5  # Number of examples to show per page
#             total_pages = (total_results + per_page - 1) // per_page if total_results > 0 else 1
#
#             # Format examples for the first page with the original word
#             formatted_examples = format_examples(examples_response, page=0, per_page=per_page, original_word=word)
#
#             # Store examples data in state
#             await state.update_data(
#                 examples_response=examples_response,
#                 current_page=0,
#                 total_pages=total_pages,
#                 per_page=per_page,
#                 word=word
#             )
#
#             # Update the existing message with the examples page
#             if total_results > 0:
#                 await query.message.edit_text(
#                     formatted_examples,
#                     reply_markup=examples_keyboard(current_page=0, total_pages=total_pages)
#                 )
#             else:
#                 await query.message.edit_text(f"Примеров для слова <b>{word}</b> не найдено.")
#
#         except Exception as e:
#             await query.message.edit_text(f"Ошибка при получении примеров: {str(e)}")
#     else:
#         await query.message.edit_text("Не удалось получить информацию о текущем слове.")
#
# # Handle next_page button callback
# @dictionary_router.callback_query(F.data == "next_page")
# async def next_page(query: CallbackQuery, state: FSMContext):
#     await query.answer()
#
#     # Get current data from state
#     data = await state.get_data()
#     current_page = data.get("current_page", 0)
#     total_pages = data.get("total_pages", 1)
#     per_page = data.get("per_page", 5)
#     examples_response = data.get("examples_response", {})
#
#     # Calculate next page (with wraparound)
#     next_page = current_page + 1
#     if next_page >= total_pages:
#         next_page = 0
#
#     # Update state with new page
#     await state.update_data(current_page=next_page)
#
#     # Format and show the next page of examples with the original word
#     word = data.get("word", "")
#     formatted_examples = format_examples(examples_response, page=next_page, per_page=per_page, original_word=word)
#
#     await query.message.edit_text(
#         formatted_examples,
#         reply_markup=examples_keyboard(current_page=next_page, total_pages=total_pages)
#     )
#
# # Handle previous_page button callback
# @dictionary_router.callback_query(F.data == "previous_page")
# async def previous_page(query: CallbackQuery, state: FSMContext):
#     await query.answer()
#
#     # Get current data from state
#     data = await state.get_data()
#     current_page = data.get("current_page", 0)
#     total_pages = data.get("total_pages", 1)
#     per_page = data.get("per_page", 5)
#     examples_response = data.get("examples_response", {})
#
#     # Calculate previous page (with wraparound)
#     prev_page = current_page - 1
#     if prev_page < 0:
#         prev_page = total_pages - 1
#
#     # Update state with new page
#     await state.update_data(current_page=prev_page)
#
#     # Format and show the previous page of examples with the original word
#     word = data.get("word", "")
#     formatted_examples = format_examples(examples_response, page=prev_page, per_page=per_page, original_word=word)
#
#     await query.message.edit_text(
#         formatted_examples,
#         reply_markup=examples_keyboard(current_page=prev_page, total_pages=total_pages)
#     )
#
# # Handle page_info button callback - just show information about navigation
# @dictionary_router.callback_query(F.data == "page_info")
# async def page_info(query: CallbackQuery):
#     await query.answer(
#         "Используйте кнопки для навигации между страницами примеров",
#         show_alert=True
#     )
#
# # Handle return_to_word button callback
# @dictionary_router.callback_query(F.data == "return_to_word")
# async def return_to_word(query: CallbackQuery, state: FSMContext):
#     await query.answer()
#
#     # Get current data from state
#     data = await state.get_data()
#     current_word_index = data.get("current_index", 0)
#     formatted_results = data.get("formatted_results", [])
#
#     # Return to the current word
#     if formatted_results and 0 <= current_word_index < len(formatted_results):
#         await query.message.edit_text(
#             formatted_results[current_word_index],
#             reply_markup=word_keyboard()
#         )
#     else:
#         await query.message.edit_text("Не удалось вернуться к слову. Пожалуйста, введите слово еще раз.")
#
# # Handle exit_vocab_mode button callback
# @dictionary_router.callback_query(F.data == "exit_vocab_mode")
# async def exit_vocab_mode_callback(query: CallbackQuery, state: FSMContext):
#     """Handler to exit the dictionary mode via inline button"""
#     await query.answer()
#     await state.clear()
#
#     await query.message.edit_text(
#         "Вы вышли из режима словаря. Используйте /vocab чтобы снова войти в режим словаря."
#     )