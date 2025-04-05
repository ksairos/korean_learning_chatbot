import logfire

from aiogram import Bot
from fastapi import FastAPI
from fastembed import SparseTextEmbedding
from openai import AsyncOpenAI
from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient, QdrantClient

from src.config.settings import Config
from src.llm_agent.agent import agent
from src.schemas.schemas import RetrieverDeps

app = FastAPI()

config = Config()
bot = Bot(token=config.bot_token)

openai_client = AsyncOpenAI()
qdrant_client = QdrantClient(
    host=config.qdrant_host_docker,
    port=config.qdrant_port,
)


logfire.configure(token=config.logfire_api_key)
logfire.instrument_openai(openai_client)
logfire.instrument_fastapi(app)

class Message(BaseModel):
    user_prompt: str

@app.get("/")
async def root():
    return {"message" : "API"}


@app.post("/invoke")
async def process_message(message: Message):

    logfire.info(f'User message "{message}"')
    deps = RetrieverDeps(
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        sparse_embedding=SparseTextEmbedding(config.sparse_embedding_model),
    )

    response = await agent.run(message.user_prompt, deps=deps)
    logfire.info("Response: {response}", response=response.data)
    return {"response" : response.data}