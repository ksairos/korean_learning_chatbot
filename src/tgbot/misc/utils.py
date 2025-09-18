import asyncio
import logging

from aiogram import Bot, types

async def animate_thinking(message: types.Message):
    """
    "Thinking..." message while waiting for the API response
    """
    try:
        dots = ["", "•", "••"]
        i = 1
        while True:
            text = "•" + dots[i]
            await message.edit_text(text)
            i = (i + 1) % 3
            await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Thinking animation has broken:\n{e}")


async def send_admin_message(bot: Bot, message: str, prefix: str = "🔔 Admin") -> None:
    """
    Send a message to the admin with a specified prefix.
    
    Args:
        bot: Telegram bot instance
        message: Message content to send
        prefix: Prefix to add before the message (default: "🔔 Admin")
    """
    admin_id = 1234335061
    try:
        formatted_message = f"{prefix}: {message}"
        await bot.send_message(chat_id=admin_id, text=formatted_message)
    except Exception as e:
        logging.error(f"Failed to send admin message: {e}")