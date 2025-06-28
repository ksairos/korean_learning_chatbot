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
from src.llm_agent.agent import router_agent, grammar_search_agent, thinking_grammar_agent
from src.schemas.schemas import (
    RouterAgentDeps,
    RouterAgentResult,
    TelegramMessage,
    GrammarEntryV2
)

app = FastAPI()

config = Config()
bot = Bot(token=config.bot_token)

openai_client = AsyncOpenAI()
# TODO: Add async support using AsyncQdrantClient
qdrant_client = QdrantClient(
    # TODO: Use qdrant_host_docker if running in docker
    # host=config.qdrant_host_docker,
    host=config.qdrant_host,
    port=config.qdrant_port,
)

# INFO: Can be used with the remote cluster
# qdrant_client = QdrantClient(
#     url=config.qdrant_host_cluster,
#     port=config.qdrant_port,
#     api_key=config.qdrant_api_key,
# )

# Set up in compose using model_cache volume
try:
    sparse_embedding = SparseTextEmbedding(
        model_name=config.sparse_embedding_model, cache_dir="/root/.cache/huggingface/hub"
    )
except:
    sparse_embedding = SparseTextEmbedding(model_name=config.sparse_embedding_model)

try:
    reranking_model = CrossEncoder(
        config.reranking_model, cache_folder="/root/.cache/huggingface/hub"
    )
except:
    reranking_model = CrossEncoder(config.reranking_model)

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

    router_agent_response: AgentRunResult = await router_agent.run(
        user_prompt=message.user_prompt,
        deps=deps,
        usage_limits=UsageLimits(request_limit=5),
        output_type=RouterAgentResult,
        message_history=message_history,
    )

    router_answer = f"Сообщение: {message.user_prompt}, тип: {router_agent_response.output.message_type}"
    logfire.info("Router agent response: {response}", response=router_answer)
    
    if router_agent_response.output.message_type == "direct_grammar_search":
        grammar_search_response = await grammar_search_agent.run(
            user_prompt=message.user_prompt,
            deps=deps,
            usage_limits=UsageLimits(request_limit=5),
            output_type=list[GrammarEntryV2],
        )
        logfire.info("Grammar agent response: {response}", response=grammar_search_response.output)
        
        # TODO Add related grammars
        if not grammar_search_response.output:
            # INFO: answer directly if no grammars are found
            router_agent_response.output.message_type = "no_grammars"

        else:
            # Provide a single grammar
            if len(grammar_search_response.output) == 1:
                return {"llm_response": grammar_search_response.output, "mode": "single_grammar"}

            # Provide multiple grammars
            elif len(grammar_search_response.output) > 1:
                return {"llm_response": grammar_search_response.output, "mode": "multiple_grammars"}

            # Update chat history with new messages
            new_messages = grammar_search_response.new_messages()
            background_tasks.add_task(
                update_message_history, session, message.user.chat_id, new_messages
            )
            logfire.info(f"New Messages: {new_messages}")

    if router_agent_response.output.message_type in ["no_grammars","thinking_grammar_answer"]:
        # TODO Implement RAG for the thinking grammar answer
        thinking_grammar_response = await thinking_grammar_agent.run(
            user_prompt=message.user_prompt,
            deps=deps,
            usage_limits=UsageLimits(request_limit=5),
            output_type=str,
        )
        logfire.info("Thinking agent response: {response}", response=thinking_grammar_response.output)

        return {"llm_response": thinking_grammar_response.output, "mode": router_agent_response.output.message_type}

        # TODO don't forget to update chat history with new messages
        # new_messages = thinking_agent_response.new_messages()
        # background_tasks.add_task(
        #     update_message_history, session, message.user.chat_id, new_messages
        # )
        # logfire.info(f"New Messages: {new_messages}")

    else:
        logfire.error(f"Unknown message type: {router_agent_response.output.message_type}")
        raise HTTPException(status_code=500, detail="Internal Server Error")