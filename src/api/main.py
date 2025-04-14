import logfire

from aiogram import Bot
from fastapi import FastAPI
from fastapi.params import Depends
from fastembed import SparseTextEmbedding
from sentence_transformers import CrossEncoder
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai.usage import UsageLimits
from qdrant_client import AsyncQdrantClient, QdrantClient
from sqlalchemy.orm import Session

from src.config.settings import Config
from src.db.database import get_db
from src.llm_agent.agent import router_agent
from src.schemas.schemas import RouterAgentDeps, RouterAgentResult

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
reranking_model = CrossEncoder(config.reranking_model)


logfire.configure(token=config.logfire_api_key)
logfire.instrument_openai(openai_client)
logfire.instrument_fastapi(app)

class Message(BaseModel):
    user_prompt: str

@app.get("/")
async def root():
    return {"message" : "API"}


@app.post("/invoke")
async def process_message(message: Message, db: Session = Depends(get_db)):

    logfire.info(f'User message "{message}"')
    
    
    deps = RouterAgentDeps(
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        sparse_embedding=sparse_embedding,
        reranking_model=reranking_model,
        db=db
    )
    
    response = await router_agent.run(
        user_prompt=message.user_prompt,
        deps=deps,
        usage_limits=UsageLimits(request_limit=5),
        result_type=RouterAgentResult
    )

    # response = await grammar_agent.run(message.user_prompt, deps=deps)
    logfire.info("Response: {response}", response=response.data)
    return {
        "llm_response" : response.data.llm_response,
        "mode" : response.data.mode
    }