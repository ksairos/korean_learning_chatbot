import asyncio
import logging

from aiogram import types

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