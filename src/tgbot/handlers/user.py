from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from chatgpt_md_converter import telegram_format

user_router = Router()

# TODO Handle adding new users to the database after /start command
@user_router.message(CommandStart())
async def user_start(message: Message):
    """Handle the /start command"""
    await message.reply(
        telegram_format(
            "Приветствую! Я - LazyHangeul, твой помощник в изучении корейской грамматики.\n"
            "Какую грамматику тебе объяснить?\n\n"
            "Hello! I'm LazyHangeul, your Korean grammar learning assistant\n"
            "Which grammar would you like to learn today?"
        )
    )