import logfire

import betterlogging as bl
from aiogram import Bot
from fastapi import FastAPI
from pydantic import BaseModel

from src.config.settings import Config
from src.llm_agent.agent import agent

app = FastAPI()
logfire.configure(send_to_logfire="if-token-present")

config = Config()
bot = Bot(token=config.tg_bot.bot_token)

class Message(BaseModel):
    user_prompt: str

@app.get("/")
async def root():
    return {"message" : "API"}


@app.post("/query")
async def process_message(message: Message):
    response = await agent.run(message.user_prompt)
    logfire.info("Response: {response}", response=response.data)
    return {"response" : response.data}