from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from chatgpt_md_converter import telegram_format

from src.db.crud import add_user, clear_chat_history
from src.schemas.schemas import TelegramUser
from src.db.database import async_session
from src.tgbot.misc.utils import send_admin_message

user_router = Router()

@user_router.message(CommandStart())
async def user_start(message: Message):
    """Handle the /start command"""
    await message.answer(
        telegram_format(
            "✨ Давай вместе повторять или изучать корейский язык!\n\n"
            "Слева внизу есть меню - выбери то, что тебе интересно.\n\n"
            "Моя основная цель - помочь тебе разобраться с грамматикой.\n"
            "Но, помимо этого, мы можем просто пообщаться на корейском, как настоящие друзья, или я помогу перевести нужное тебе предложение."
        )
    )

    user_info = f"@{message.from_user.username or 'N/A'} (ID: {message.from_user.id})"
    await send_admin_message(
        message.bot, f"{user_info} стартовал бота", "⚠️ Стартовал Бота"
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
        async with async_session() as session:
            await add_user(session=session, user=user)
            user_info = f"@{message.from_user.username or 'N/A'} (ID: {message.from_user.id})"
            await send_admin_message(message.bot, f"{user_info} получил доступ к боту", "🙋New User")
        await message.answer("Доступ предоставлен! Теперь вы можете использовать бота.")
    except Exception as e:
        await message.answer("Произошла ошибка при предоставлении доступа.")
        import logging
        logging.error(f"Error adding user {user.user_id}: {e}")


@user_router.message(Command("restart"))
async def clear_user_history(message: Message, state: FSMContext):
    """Handle the /restart command"""
    user = TelegramUser(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        chat_id=message.chat.id
    )
    
    try:
        async with async_session() as session:
            await clear_chat_history(session, user)
            
        # Clear any active FSM state as well
        await state.clear()
        await message.answer("История чата очищена! Чем я могу помочь?")
            
    except Exception as e:
        await message.answer("Произошла ошибка, попробуйте снова")
        # Log the error
        import logging
        logging.error(f"Error clearing chat history for user {user.user_id}: {e}")


@user_router.message(Command("grammar"))
async def grammar_command(message: Message):
    """Handle the /grammar command"""
    await message.answer(
        "Про какую грамматику ты хочешь узнать больше? Можешь написать её на корейском (прим.: 으니까) или примерное значение на русском (прим.: конструкции причины)."
    )


@user_router.message(Command("conversation"))
async def conversation_command(message: Message):
    """Handle the /conversation command"""
    await message.answer(
        "Представь, что я твой корейский друг, с которым можно вести диалог 😻\n\n"
        "Можешь попросить меня исправлять ошибки или наоборот игнорировать их.\n\n"
        "- 안녕하세요?\n"
        "- 봇이라고 해요~ 반가워요!\n"
        "- 이름이 뭐예요?"
    )


@user_router.message(Command("translate"))
async def translate_command(message: Message):
    """Handle the /translate command"""
    await message.answer(
        "В этом режиме можешь присылать мне сообщения на русском, чтобы я перевел их на корейской и на корейском, чтобы увидеть перевод на русском"
    )