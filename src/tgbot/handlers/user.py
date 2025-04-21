from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.tgbot.keyboards.inline import get_main_menu_keyboard

user_router = Router()

# TODO Handle adding new users to the database after /start command
@user_router.message(CommandStart())
async def user_start(message: Message):
    """Handle the /start command"""
    await message.reply("Приветствую! Я - виртуальный ассистент по изучению корейского",
                        reply_markup=get_main_menu_keyboard())