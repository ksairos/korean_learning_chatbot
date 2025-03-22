import logging

import betterlogging as bl
import fastapi
from aiogram import Bot
from fastapi import FastAPI
from starlette.responses import JSONResponse
from pydantic import BaseModel

from tgbot.config import load_config, Config

app = FastAPI()
log_level = logging.INFO
bl.basic_colorized_config(level=log_level)
log = logging.getLogger(__name__)

config: Config = load_config(".env")
bot = Bot(token=config.tg_bot.token)


class MessageRequest(BaseModel):
    user_id: int
    message_text: str


@app.get("/")
async def root():
    return {"message" : "API"}

@app.post("/api")
async def webhook_endpoint(request: fastapi.Request):
    return JSONResponse(status_code=200, content={"status": "ok"})


@app.post("/process_message")
async def process_message(request: MessageRequest):
    """
    Process messages from the Telegram bot.
    This endpoint receives messages from users and returns responses.
    """
    try:
        # Log the incoming request
        log.info(f"Received message from user {request.user_id}: {request.message_text}")
        
        # Process the message (this is where you'd implement your logic)
        # Example: Simple echo with Korean greeting
        if request.message_text.lower() in ["hello", "hi", "안녕", "안녕하세요"]:
            response = "안녕하세요! (Hello!) How can I help you with Korean today?"
        else:
            # Here you could integrate with a language model, database, or other services
            response = f"You said: '{request.message_text}'\n\nI'm still learning how to process Korean language requests."
        
        # Return the response to the bot
        return JSONResponse(
            status_code=200,
            content={"response": response}
        )
    except Exception as e:
        log.exception(f"Error processing message: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )
