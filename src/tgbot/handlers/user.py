from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from src.tgbot.keyboards.inline import get_main_menu_keyboard

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message):
    await message.reply("Welcome to the Korean Learning Bot! Use the menu to navigate.", 
                        reply_markup=get_main_menu_keyboard())