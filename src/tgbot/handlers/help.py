from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.tgbot.keyboards.inline import get_main_menu_keyboard

help_router = Router()


@help_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handler for the /help command"""
    help_text = (
        "<b>Korean Learning Bot - Help</b>\n\n"
        "This bot helps you learn Korean vocabulary and practice writing.\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Start the bot\n"
        "/vocab - Запустить режим словаря\n"
        "/help - Show this help message\n\n"
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())