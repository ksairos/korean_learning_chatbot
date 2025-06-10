import json
import logfire

from aiogram import Bot
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.params import Depends
from fastembed import SparseTextEmbedding
from sentence_transformers import CrossEncoder
from openai import AsyncOpenAI
from pydantic_ai.usage import UsageLimits
from pydantic_ai.agent import AgentRunResult
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Config
from src.db.crud import get_message_history, update_message_history, get_user_ids
from src.db.database import get_db
from src.llm_agent.agent import router_agent
from src.schemas.schemas import RouterAgentDeps, RouterAgentResult, TelegramMessage

app = FastAPI()

config = Config()
bot = Bot(token=config.bot_token)

openai_client = AsyncOpenAI()
# TODO: Add async support using AsyncQdrantClient
qdrant_client = QdrantClient(
    host=config.qdrant_host_docker,
    port=config.qdrant_port,
)

# NOTE: Can be used with the remote cluster

# qdrant_client = QdrantClient(
#     url=config.qdrant_host_cluster,
#     port=config.qdrant_port,
#     api_key=config.qdrant_api_key,
# )

# Set up in compose using model_cache volume
sparse_embedding = SparseTextEmbedding(
    model_name=config.sparse_embedding_model, cache_dir="/root/.cache/huggingface/hub"
)
reranking_model = CrossEncoder(
    config.reranking_model, cache_folder="/root/.cache/huggingface/hub"
)


logfire.configure(token=config.logfire_api_key)
logfire.instrument_openai(openai_client)
logfire.instrument_fastapi(app)


@app.get("/")
async def root():
    return {"message": "API"}


@app.post("/invoke")
async def process_message(
    message: TelegramMessage,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    logfire.info(f'User message "{message}"')

    allowed_users = await get_user_ids(session)
    if message.user.user_id not in allowed_users:
        raise HTTPException(status_code=403,
                            detail="User not registered")

    deps = RouterAgentDeps(
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        sparse_embedding=sparse_embedding,
        reranking_model=reranking_model,
        session=session,
    )

    # Retrieve message history if present
    message_history = await get_message_history(session, message.user, 5)

    response: AgentRunResult = await router_agent.run(
        user_prompt=message.user_prompt,
        deps=deps,
        usage_limits=UsageLimits(request_limit=5),
        output_type=RouterAgentResult,
        message_history=message_history,
    )

    # Update chat history with new messages
    new_messages = response.new_messages_json()
    background_tasks.add_task(
        update_message_history, session, message.user.chat_id, new_messages
    )

    logfire.info(f"New Messages: {json.loads(new_messages.decode("utf-8"))}")

    logfire.info("Response: {response}", response=response.output)
    return {"llm_response": response.output.llm_response, "mode": response.output.mode}