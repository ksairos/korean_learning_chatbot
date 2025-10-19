import asyncio
import logging

import betterlogging as bl
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.client.default import DefaultBotProperties

from src.config.settings import Config
from src.tgbot.handlers import routers_list
from src.tgbot.middlewares.config import ConfigMiddleware
from src.tgbot.misc.utils import send_admin_message


async def on_startup(bot: Bot, admin_ids: list[int]):
    # Set up the main menu button that appears next to the message input field
    from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
    
    # Сюда добавляются команды для кнопки Menu (слева от поля ввода)
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Что я могу?"),
        BotCommand(command="restart", description="Начать новый чат"),
        BotCommand(command="grammar", description="Изучение грамматики"),
        BotCommand(command="conversation", description="Разговорная практика"),
        BotCommand(command="translate", description="Режим переводчика")
    ]

    admin_commands = [
        BotCommand(command="users", description="List all users in the DB"),
        BotCommand(command="restart", description="Clear chat history"),
        BotCommand(command="help", description="Show help information"),
        BotCommand(command="status", description="Show bot and system status"),
        BotCommand(command="deleteuser", description="Delete user by ID"),
        BotCommand(command="history", description="Get user chat history by ID"),
    ]

    # Устанавливаем команды в определенных чатах (все чаты)
    # Если выбрать scope=BotCommandScopeChat, то команды будут доступны только в определенных чатах
    # Если выбрать scope=BotCommandScopeAllPrivateChats, то команды будут доступны во всех чатах с ботом
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    for admin_id in admin_ids:
        await bot.set_my_commands(
            admin_commands, scope=BotCommandScopeChat(chat_id=admin_id)
        )
    
    # Notify admins that the bot has started
    await send_admin_message(bot, "The bot is up", prefix="✅")


def register_global_middlewares(dp: Dispatcher, config: Config, session_pool=None):
    """
    Register global middlewares for the given dispatcher.
    Global middlewares here are the ones that are applied to all the handlers (you specify the type of update)

    :param dp: The dispatcher instance.
    :type dp: Dispatcher
    :param config: The configuration object from the loaded configuration.
    :param session_pool: Optional session pool object for the database using SQLAlchemy.
    :return: None
    """
    middleware_types = [
        ConfigMiddleware(config),
        # DatabaseMiddleware(session_pool),
    ]

    for middleware_type in middleware_types:
        dp.message.outer_middleware(middleware_type)
        dp.callback_query.outer_middleware(middleware_type)


def setup_logging():
    """
    Set up logging configuration for the application.

    This method initializes the logging configuration for the application.
    It sets the log level to "info" and configures a basic colorized log for
    output. The log format includes the filename, line number, log level,
    timestamp, logger name, and log message.

    Returns:
        None

    Example usage:
        setup_logging()
    """
    log_level = logging.INFO
    bl.basic_colorized_config(level=log_level)

    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting bot")


def get_storage(config):
    """
    Return storage based on the provided configuration.

    Args:
        config (Config): The configuration object.

    Returns:
        Storage: The storage object based on the configuration.

    """
    # TODO Configure for Redis
    if config.use_redis:
        return RedisStorage.from_url(
            config.redis.dsn(),
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    else:
        return MemoryStorage()


async def main():
    setup_logging()

    config = Config()
    storage = get_storage(config)

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    dp.include_routers(*routers_list)

    register_global_middlewares(dp, config)

    await on_startup(bot, config.admin_ids)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("The bot is turned off")
