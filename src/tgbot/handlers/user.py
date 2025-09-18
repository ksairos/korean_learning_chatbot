from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from chatgpt_md_converter import telegram_format

from src.db.crud import add_user, clear_chat_history
from src.schemas.schemas import TelegramUser
from src.db.database import get_db
from src.tgbot.misc.utils import send_admin_message

user_router = Router()

@user_router.message(CommandStart())
async def user_start(message: Message):
    """Handle the /start command"""
    await message.answer(
        telegram_format(
            "Приветствую! Я - LazyHangeul, ИИ ассистент в изучении корейской грамматики на базе OpenAI. "
            "Помогу в поиске нужной грамматики или отвечу на вопросы связанные с ней /help\n\n"
            "В данный момент чатбот находится в разработке, чтобы получить доступ, обратитесь автору для получения доступа. \n\nТГ: @ksairosdormu"
        )
    )

    user_info = f"@{message.from_user.username or 'N/A'} (ID: {message.from_user.id})"
    await send_admin_message(
        message.bot, f"{user_info} стартовал бота", "🙋 Стартовал Бота"
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


@user_router.message(Command("givemebotaccess"))
async def give_bot_access(message: Message):
    """Handle the /givemebotaccess command - secret command to register user"""
    user = TelegramUser(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        chat_id=message.chat.id
    )
    
    try:
        async for session in get_db():
            await add_user(session=session, user=user)
            user_info = f"@{message.from_user.username or 'N/A'} (ID: {message.from_user.id})"
            await send_admin_message(message.bot, f"{user_info} получил доступ к боту", "🙋🆕 New User")
        await message.answer("Доступ предоставлен! Теперь вы можете использовать бота.")
    except Exception as e:
        await message.answer("Произошла ошибка при предоставлении доступа.")
        import logging
        logging.error(f"Error adding user {user.user_id}: {e}")


@user_router.message(Command("clear_history"))
async def clear_user_history(message: Message, state: FSMContext):
    """Handle the /clear_history command"""
    user = TelegramUser(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        chat_id=message.chat.id
    )
    
    try:
        async for session in get_db():
            await clear_chat_history(session, user)
            
        # Clear any active FSM state as well
        await state.clear()
        await message.answer(f"История чата очищена!")
            
    except Exception as e:
        await message.answer("Произошла ошибка, попробуйте снова")
        # Log the error
        import logging
        logging.error(f"Error clearing chat history for user {user.user_id}: {e}")