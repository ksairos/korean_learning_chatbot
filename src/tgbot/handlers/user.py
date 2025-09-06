from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from chatgpt_md_converter import telegram_format

from src.db.crud import add_user
from src.schemas.schemas import TelegramUser
from src.db.database import get_db

user_router = Router()

@user_router.message(CommandStart())
async def user_start(message: Message):
    """Handle the /start command"""
    await message.reply(
        telegram_format(
            "Приветствую! Я - LazyHangeul, твой ИИ ассистент в изучении корейской грамматики на базе OpenAI.\n"
            "Помогу в поиске нужной грамматики или отвечу на вопросы связанные с ней\n\n"
            "В данный момент чатбот находится в разработке, чтобы получить доступ, обратитесь автору для получения доступа. \n\nТГ: @ksairosdormu"
        )
    )

    # IMPORTANT Uncomment to turn on user adding with /start

    # user = TelegramUser(
    #     user_id=message.from_user.id,
    #     username=message.from_user.username,
    #     first_name=message.from_user.first_name,
    #     last_name=message.from_user.last_name,
    #     chat_id=message.chat.id
    # )
    #
    # async for session in get_db():
    #     await add_user(session=session, user=user)