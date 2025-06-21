from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.tgbot.keyboards.inline import get_main_menu_keyboard
from src.utils.json_to_telegram_md import grammar_entry_to_markdown

help_router = Router()


@help_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handler for the /help command"""
    # help_text = (
    #     "<b>Korean Learning Bot - Help</b>\n\n"
    #     "This bot helps you learn Korean vocabulary and practice writing.\n\n"
    #     "<b>Available Commands:</b>\n"
    #     "/start - Start the bot\n"
    #     "/vocab - Запустить режим словаря\n"
    #     "/help - Show this help message\n\n"
    # )
    # await message.answer(help_text, reply_markup=get_main_menu_keyboard())
    
    foo =   {
    'grammar_name_kr': '까지', 
    'grammar_name_rus': '«до»', 
    'level': 1, 
    'content': '**Описание:**\nЧастица **까지** используется для обозначения предела действия или состояния в значении **«до»**. Может указывать как на **временные границы** (до какого времени), так и на **пространственные пределы** (до какого места).\n\n**Форма:**\n**Существительное + 까지**\nПрисоединяется непосредственно к существительному, обозначающему время или место.\n\n**Примеры:**\n학교**까지** 걸어서 갔어요.\nЯ пошёл до школы пешком.\n\n밤 12시**까지** 공부했어요.\nУчился до полуночи.\n\n부산**까지** 기차로 가요.\nДо Пусана еду на поезде.\n\n이번 주 금요일**까지** 숙제를 내세요.\nСдайте домашнее задание до этой пятницы.\n\n**Примечания:**\n\n1. Часто используется вместе с **부터** (с): **부터 … 까지** - «от … до» - если говорить о времени.\n    **Например:**\n\n오전 9시**부터** 오후 5시**까지** 일해요.\nРаботаю с 9 утра до 5 вечера.\n\n1. Часто используется вместе с **에서** (из): **에서 … 까지** - «из … до» - если говорить о местах.\n    **Например:**\n\n서울**에서** 경주**까지** 기차로 왔어요.\n\nДоехал из Сеула до Кёнджу на поезде.\n\n1. Может использоваться не только в буквальном, но и в переносном смысле.\n    **Например:**\n\n너**까지** 나를 의심해?\nДаже ты меня подозреваешь?\n', 
    'related_grammars': ['부터', '에서 «из»']
    }

    # start_time = time.perf_counter()
    await message.answer(grammar_entry_to_markdown(foo))