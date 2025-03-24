import logging

import betterlogging as bl
from aiogram import Bot
from fastapi import FastAPI
from pydantic import BaseModel

from src.config.settings import Config
from src.llm_agent.agent import agent

app = FastAPI()
log_level = logging.INFO
bl.basic_colorized_config(level=log_level)
log = logging.getLogger(__name__)

config = Config()
bot = Bot(token=config.tg_bot.bot_token)

class Message(BaseModel):
    user_prompt: str

@app.get("/")
async def root():
    return {"message" : "API"}


@app.post("/query")
async def process_message(message: Message):
    response = await agent.query(message.user_prompt)
    return {"llm_response" : response}