import logfire

from aiogram import Bot
from fastapi import FastAPI
from pydantic import BaseModel

from src.config.settings import Config
from src.llm_agent.agent import agent

app = FastAPI()

config = Config()
bot = Bot(token=config.bot_token)

logfire.configure(token=config.logfire_api_key)
logfire.instrument_fastapi(app)

class Message(BaseModel):
    user_prompt: str

@app.get("/")
async def root():
    return {"message" : "API"}


@app.post("/invoke")
async def process_message(message: Message):
    response = await agent.run(message.user_prompt)
    logfire.info("Response: {response}", response=response.data)
    return {"response" : response.data}