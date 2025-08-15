import logfire
import os

from aiogram import Bot
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.params import Depends
from fastembed import SparseTextEmbedding, LateInteractionTextEmbedding
from sentence_transformers import CrossEncoder
from openai import AsyncOpenAI
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.usage import UsageLimits
from pydantic_ai.agent import AgentRunResult
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Config
from src.db.crud import get_message_history, update_message_history, get_user_ids
from src.db.database import get_db
from src.llm_agent.agent import router_agent, query_rewriter_agent, thinking_grammar_agent, system_agent, hyde_agent
from src.llm_agent.agent_tools import retrieve_grammars_tool, retrieve_docs_tool
from src.schemas.schemas import (
    RouterAgentDeps,
    RouterAgentResult,
    TelegramMessage,
    GrammarEntryV2, RetrievedDoc
)

app = FastAPI()

config = Config()
bot = Bot(token=config.bot_token)

cache_directory = os.path.expanduser("~/.cache/huggingface/hub")

openai_client = AsyncOpenAI()
# TODO: Add async support using AsyncQdrantClient
qdrant_client = QdrantClient(
    # IMPORTANT: Use qdrant_host_docker if running in docker
    # host=config.qdrant_host_docker,
    host=config.qdrant_host,
    port=config.qdrant_port,
)

logfire.configure(token=config.logfire_api_key, environment="local")
logfire.instrument_openai(openai_client)
logfire.instrument_fastapi(app)
logfire.instrument_pydantic_ai()

# INFO: Can be used with the remote cluster
# qdrant_client = QdrantClient(
#     url=config.qdrant_host_cluster,
#     port=config.qdrant_port,
#     api_key=config.qdrant_api_key,
# )

# Set up in compose using model_cache volume
# FIXME: Check out the cache folder location. Substitute with another option, as it is now not a volume in the compose
# FIXME: Use 3_create_qdrant_rag_collection.ipynb as a reference
try:
    sparse_embedding = SparseTextEmbedding(
        model_name=config.sparse_embedding_model,
        cache_dir=cache_directory,
        local_files_only=True
    )
except:
    sparse_embedding = SparseTextEmbedding(model_name=config.sparse_embedding_model)

try:
    reranking_model = CrossEncoder(
        config.reranking_model,
        cache_folder=cache_directory,
        local_files_only=True
    )
except:
    reranking_model = CrossEncoder(config.reranking_model)

try:
    late_interaction_model = LateInteractionTextEmbedding(
        config.late_interaction_model,
        cache_dir=cache_directory,
        local_files_only=True
    )
except Exception as e:
    late_interaction_model = LateInteractionTextEmbedding(config.late_interaction_model)


@app.get("/")
async def root():
    return {"message": "API"}

@app.post("/invoke")
async def process_message(
    message: TelegramMessage,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    local_logfire = logfire.with_tags(str(message.user.user_id))
    local_logfire.info(f'User message "{message}"')

    mode = "casual_answer"

    # IMPORTANT: Check if user is registered
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
    message_history = await get_message_history(session, message.user)

    router_agent_response: AgentRunResult = await router_agent.run(
        user_prompt=message.user_prompt,
        usage_limits=UsageLimits(request_limit=5),
        output_type=RouterAgentResult,
        # message_history=message_history,
    )

    router_answer = f"Сообщение: {message.user_prompt}, тип: {router_agent_response.output.message_type}"
    local_logfire.info(
        "Router agent response: {response}",
        response=router_answer,
    )

    if router_agent_response.output.message_type == "direct_grammar_search":
        # TODO: Uncomment message history
        query_rewriter_response = await query_rewriter_agent.run(
            user_prompt=message.user_prompt,
            usage_limits=UsageLimits(request_limit=5)
            # message_history=message_history,
        )
        local_logfire.info(f"Rewritten query: {query_rewriter_response.output}")
        
        # TODO Add related grammars
        if not query_rewriter_response.output:
            # INFO: answer directly if no grammars are found
            mode = "no_grammar"
            router_agent_response.output.message_type = "thinking_grammar_answer"

        else:

            retrieved_grammars = await retrieve_grammars_tool(deps, query_rewriter_response.output)

            # Provide a single grammar
            if len(retrieved_grammars) == 1:
                mode = "single_grammar"
                return {"llm_response": retrieved_grammars, "mode": mode}

            # Provide multiple grammars
            elif len(retrieved_grammars) > 1:
                mode = "multiple_grammars"
                return {"llm_response": retrieved_grammars, "mode": mode}

            # Update chat history with new messages
            new_messages = query_rewriter_response.new_messages()
            background_tasks.add_task(
                update_message_history, session, message.user, new_messages
            )
            local_logfire.info(f"New Messages: {new_messages}")

    if router_agent_response.output.message_type == "thinking_grammar_answer":

        hyde_response = await hyde_agent.run(user_prompt=message.user_prompt)
        # FIXME: Add reranking method
        retrieved_docs: list[RetrievedDoc | None] = await retrieve_docs_tool(deps, hyde_response.output)

        docs = [doc.content["content"] for doc in retrieved_docs if doc]

        thinking_grammar_response = await thinking_grammar_agent.run(
            user_prompt=message.user_prompt,
            deps=docs,
            usage_limits=UsageLimits(request_limit=5),
            output_type=str,
            # message_history=message_history,
        )
        local_logfire.info("Thinking agent response: {response}", response=thinking_grammar_response.output, _tags=[""])

        # "mode" will be "no_grammar" only if message type was converted from direct_grammar_search
        if not mode == "no_grammar":
            mode = "thinking_grammar_answer"

        return {"llm_response": thinking_grammar_response.output, "mode": mode}

        # TODO don't forget to update chat history with new messages
        # new_messages = thinking_agent_response.new_messages()
        # background_tasks.add_task(
        #     update_message_history, session, message.user.chat_id, new_messages
        # )
        # local_logfire.info(f"New Messages: {new_messages}")

    if router_agent_response.output.message_type == "casual_answer":
        casual_response = await system_agent.run(
            user_prompt=message.user_prompt,
            usage_limits=UsageLimits(request_limit=5),
            output_type=str,
            # message_history=message_history,
        )
        local_logfire.info("System agent response: {response}", response=casual_response.output)

        mode = "casual_answer"
        return {"llm_response": casual_response.output, "mode": mode}


    else:
        local_logfire.error(f"Unknown message type: {router_agent_response.output.message_type}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/evaluate/test1")
async def evaluate_rag_1(
    message: TelegramMessage,
    session: AsyncSession = Depends(get_db),
):
    local_logfire = logfire.with_tags(str(message.user.user_id), "evaluation", "test1")
    local_logfire.info(f'User message "{message}"')

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

    hyde_response = await hyde_agent.run(user_prompt=message.user_prompt)
    retrieved_docs: list[RetrievedDoc | None] = await retrieve_docs_tool(
        deps,
        hyde_response.output,
        search_strategy="hybrid",
        rerank_strategy="cross"
    )
    docs = [doc.content["content"] for doc in retrieved_docs if doc]

    local_logfire.info(f"Retrieved docs: {docs}", _tags=["Evaluation"])

    thinking_grammar_response = await thinking_grammar_agent.run(
        user_prompt=message.user_prompt,
        deps=docs,
        usage_limits=UsageLimits(request_limit=5),
    )

    local_logfire.info("Thinking agent response: {response}", response=thinking_grammar_response.output, _tags=[""])

    return {"llm_response": thinking_grammar_response.output, "retrieved_docs": retrieved_docs}

    # return {"llm_response": thinking_grammar_response.new_messages_json().decode()}


@app.post("/evaluate/test2")
async def evaluate_rag_2(
    message: TelegramMessage,
    session: AsyncSession = Depends(get_db),
):
    local_logfire = logfire.with_tags(str(message.user.user_id), "evaluation", "test2")
    local_logfire.info(f'User message: "{message}"')

    allowed_users = await get_user_ids(session)
    if message.user.user_id not in allowed_users:
        raise HTTPException(status_code=403,
                            detail="User not registered")

    deps = RouterAgentDeps(
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        sparse_embedding=sparse_embedding,
        reranking_model=reranking_model,
        late_interaction_model=late_interaction_model,
        session=session,
    )

    hyde_response = await hyde_agent.run(user_prompt=message.user_prompt)
    retrieved_docs: list[RetrievedDoc | None] = await retrieve_docs_tool(
        deps,
        hyde_response.output,
        search_strategy="hybrid",
        rerank_strategy="colbert"
    )
    docs = [doc.content["content"] for doc in retrieved_docs if doc]

    local_logfire.info(f"Retrieved docs: {docs}", _tags=["Evaluation"])

    thinking_grammar_response = await thinking_grammar_agent.run(
        user_prompt=message.user_prompt,
        deps=docs,
        usage_limits=UsageLimits(request_limit=5),
    )

    local_logfire.info("Thinking agent response: {response}", response=thinking_grammar_response.output, _tags=[""])

    return {"llm_response": thinking_grammar_response.output, "retrieved_docs": retrieved_docs}