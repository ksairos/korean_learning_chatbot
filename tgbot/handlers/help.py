from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from tgbot.keyboards.inline import get_main_menu_keyboard

help_router = Router()


@help_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handler for the /help command"""
    help_text = (
        "<b>Korean Learning Bot - Help</b>\n\n"
        "This bot helps you learn Korean vocabulary and practice writing.\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Start the bot\n"
        "/menu - Show the main menu\n"
        "/help - Show this help message\n\n"
        "<b>Main Features:</b>\n"
        "• Learn Korean vocabulary\n"
        "• Practice writing Korean characters\n"
        "• Take daily challenges\n"
        "• Track your learning progress\n\n"
        "Use the menu button below to navigate the bot's features."
    )
    await message.reply(help_text, reply_markup=get_main_menu_keyboard())


@help_router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Handler for the help button in the inline keyboard"""
    help_text = (
        "<b>Korean Learning Bot - Help</b>\n\n"
        "This bot helps you learn Korean vocabulary and practice writing.\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Start the bot\n"
        "/menu - Show the main menu\n"
        "/help - Show this help message\n\n"
        "<b>Main Features:</b>\n"
        "• Learn Korean vocabulary\n"
        "• Practice writing Korean characters\n"
        "• Take daily challenges\n"
        "• Track your learning progress\n\n"
        "Use the menu button below to navigate the bot's features."
    )
    await callback.message.edit_text(help_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()