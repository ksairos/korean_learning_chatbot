from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.db.crud import add_user
from src.schemas.schemas import TelegramUser
from src.tgbot.filters.admin import AdminFilter
from src.db.database import get_db

admin_router = Router()
admin_router.message.filter(AdminFilter())


@admin_router.message(CommandStart())
async def admin_start(message: Message):
    admin = TelegramUser(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        chat_id=message.chat.id
    )
    async for session in get_db():
        await add_user(session=session, user=admin)

    await message.reply("Привет, админ! Добавил тебя в базу")