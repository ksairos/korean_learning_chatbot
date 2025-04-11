import logfire

from aiogram import Bot
from fastapi import FastAPI
from fastembed import SparseTextEmbedding
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai.usage import UsageLimits
from qdrant_client import AsyncQdrantClient, QdrantClient

from src.config.settings import Config
from src.llm_agent.agent import router_agent
from src.schemas.schemas import RouterAgentDeps

app = FastAPI()

config = Config()
bot = Bot(token=config.bot_token)

openai_client = AsyncOpenAI()
# TODO: Add async support using AsyncQdrantClient
qdrant_client = QdrantClient(
    host=config.qdrant_host_docker,
    port=config.qdrant_port,
)
sparse_embedding = SparseTextEmbedding(config.sparse_embedding_model)


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
    
    
    deps = RouterAgentDeps(
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        sparse_embedding=sparse_embedding,
    )
    
    response = await router_agent.run(
        user_prompt=message.user_prompt,
        deps=deps,
        usage_limits=UsageLimits(request_limit=2)
    )

    # response = await grammar_agent.run(message.user_prompt, deps=deps)
    logfire.info("Response: {response}", response=response.data)
    return {
        "response" : response.data,
    }