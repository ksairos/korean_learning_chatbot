import logging
import aiohttp
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

api_router = Router()
logger = logging.getLogger(__name__)

# This is where our FastAPI server is running
# In Docker, use the service name instead of localhost
API_URL = "http://api:8000/query"


@api_router.message(Command("ask"))
async def handle_ask_command(message: Message):
    """
    Handler for the /ask command which forwards user messages to the API
    """
    # Extract the text that comes after the /ask command
    if len(message.text.split()) > 1:
        user_query = " ".join(message.text.split()[1:])
    else:
        await message.answer("Please provide a question after the /ask command")
        return

    await process_via_api(message, user_query)

@api_router.message(F.text.startswith("!ask "))
async def handle_ask_prefix(message: Message):
    """
    Alternative way to trigger API processing with !ask prefix
    """
    user_query = message.text[5:].strip()  # Remove the "!ask " prefix
    if not user_query:
        await message.answer("Please provide a question after !ask")
        return
        
    await process_via_api(message, user_query)

async def process_via_api(message: Message, user_query: str):
    """
    Sends the user's message to the API and returns the response
    """
    # Show typing status while processing
    await message.answer_chat_action("typing")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Prepare the request payload
            payload = {
                "user_id": message.from_user.id,
                "message_text": user_query
            }
            
            # Send request to the API
            async with session.post(API_URL, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    await message.answer(data["response"])
                else:
                    logger.error(f"API error: {response.status}, {await response.text()}")
                    await message.answer("Sorry, I couldn't process your request right now.")
    except Exception as e:
        logger.exception(f"Error processing message via API: {e}")
        await message.answer("Sorry, there was an error connecting to the language processing service.")