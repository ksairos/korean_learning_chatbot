import logfire
import os

from aiogram import Bot
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.params import Depends
from fastembed import SparseTextEmbedding, LateInteractionTextEmbedding
from openai import AsyncOpenAI
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart, ModelRequest, UserPromptPart
from pydantic_ai.usage import UsageLimits
from pydantic_ai.agent import AgentRunResult
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routers import evaluation
from src.config.settings import Config
from src.db.crud import get_message_history, update_message_history, get_user_ids
from src.db.database import get_db
from src.llm_agent.agent import router_agent, thinking_grammar_agent, system_agent, query_rewriter_agent
from src.llm_agent.agent_tools import retrieve_grammars_tool, retrieve_docs_tool
from src.schemas.schemas import (
    RouterAgentDeps,
    RouterAgentResult,
    TelegramMessage,
    GrammarEntryV2, RetrievedDoc
)
from src.utils.json_to_telegram_md import grammar_entry_to_markdown

app = FastAPI()

config = Config()
bot = Bot(token=config.bot_token)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

cache_directory = os.path.expanduser("~/.cache/huggingface/hub")

openai_client = AsyncOpenAI()
# TODO: Add async support using AsyncQdrantClient
qdrant_client = AsyncQdrantClient(
    # IMPORTANT: Use qdrant_host_docker if running in docker
    # host=config.qdrant_host_docker,
    host=config.qdrant_host,
    port=config.qdrant_port,
)

logfire.configure(token=config.logfire_api_key, environment="local")
logfire.instrument_openai(openai_client)
logfire.instrument_fastapi(app)
logfire.instrument_pydantic_ai()

app.include_router(evaluation.router)

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

# try:
#     reranking_model = TextCrossEncoder(
#         model_name=config.reranking_model,
#         cache_dir=cache_directory,
#         cuda=False # TODO: change to True for prod
#     )
# except:
#     reranking_model = TextCrossEncoder(config.reranking_model)

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
        # reranking_model=reranking_model,
        session=session,
        late_interaction_model=late_interaction_model
    )

    # Retrieve message history if present
    message_history = await get_message_history(session, message.user)

    router_agent_response: AgentRunResult = await router_agent.run(
        user_prompt=message.user_prompt,
        usage_limits=UsageLimits(request_limit=3),
        output_type=RouterAgentResult,
        message_history=message_history[-2:],
    )

    router_answer = f"Сообщение: {message.user_prompt}, тип: {router_agent_response.output.message_type}"
    local_logfire.info(
        "Router agent response: {response}",
        response=router_answer,
    )

    if router_agent_response.output.message_type == "direct_grammar_search":
        query_rewriter_response = await query_rewriter_agent.run(
            user_prompt=message.user_prompt,
            usage_limits=UsageLimits(request_limit=3),
        )
        local_logfire.info(f"Rewritten query: {query_rewriter_response.output}")

        if query_rewriter_response.output == "None":
            # INFO: answer directly if no grammars are found
            mode = "no_grammar"
            router_agent_response.output.message_type = "thinking_grammar_answer"

        else:

            retrieved_grammars = await retrieve_grammars_tool(deps, query_rewriter_response.output, message.user_prompt)
            if retrieved_grammars:

                # Provide a single grammar
                if len(retrieved_grammars) == 1:
                    mode = "single_grammar"
                    response = {"llm_response": retrieved_grammars, "mode": mode}

                    # Update chat history with user message and a single grammar
                    with local_logfire.span("update_message_history"):
                        new_messages = []

                        # user_message = next(
                        #     msg for msg in query_rewriter_response.new_messages() if isinstance(msg, ModelRequest))

                        user_message = ModelRequest(parts=[UserPromptPart(content=message.user_prompt)])

                        formatted_response = grammar_entry_to_markdown(response["llm_response"][0].model_dump())
                        model_response = ModelResponse(parts=[TextPart(content=formatted_response, part_kind="text")])

                        new_messages.append(user_message)
                        new_messages.append(model_response)

                        background_tasks.add_task(update_message_history, session, message.user, new_messages)
                        local_logfire.info(f"new_messages: {new_messages}")

                # Provide multiple grammars
                else:
                    mode = "multiple_grammars"
                    response = {"llm_response": retrieved_grammars, "mode": mode}

                    # Update chat history with user message and grammar choice
                    with local_logfire.span("update_message_history"):
                        new_messages = []

                        # user_message = next(
                        #     msg for msg in query_rewriter_response.new_messages() if isinstance(msg, ModelRequest)
                        # )
                        user_message = ModelRequest(parts=[UserPromptPart(content=message.user_prompt)])

                        model_message = f"Найдено {len(retrieved_grammars)} грамматик по вашему запросу. Выберите одну:\n"
                        for i, grammar in enumerate(retrieved_grammars):
                            title = f"{grammar.grammar_name_kr.strip()} - {grammar.grammar_name_rus.strip()}\n"
                            model_message += title

                        model_response = ModelResponse(parts=[TextPart(content=model_message, part_kind="text")])

                        new_messages.append(user_message)
                        new_messages.append(model_response)

                        background_tasks.add_task(update_message_history, session, message.user, new_messages)
                        local_logfire.info(f"new_messages: {new_messages}")

                return response

            else:
                mode = "no_grammars"
                router_agent_response.output.message_type = "thinking_grammar_answer"


    if router_agent_response.output.message_type == "thinking_grammar_answer":

        # # Retrieval
        # retrieved_docs: list[RetrievedDoc | None] = await retrieve_docs_tool(
        #     deps,
        #     message.user_prompt,
        #     message_history
        # )
        # docs = [doc.content["content"] for doc in retrieved_docs if doc]

        # Generation
        # TODO: Проверить Dependencies system_prompt
        thinking_grammar_response = await thinking_grammar_agent.run(
            user_prompt=message.user_prompt,
            deps=deps,
            usage_limits=UsageLimits(request_limit=3),
            message_history=message_history,
        )
        local_logfire.info("Thinking agent response: {response}", response=thinking_grammar_response.output, _tags=[""])

        # Update chat history with new messages
        with local_logfire.span("update_message_history"):
            user_message = ModelRequest(parts=[UserPromptPart(content=message.user_prompt)])
            model_response = ModelResponse(parts=[TextPart(content=thinking_grammar_response.output)])

            # new_messages = thinking_grammar_response.new_messages()
            new_messages = [user_message, model_response]
            background_tasks.add_task(update_message_history, session, message.user, new_messages)
            local_logfire.info(f"new_messages: {new_messages}")

        # "mode" will be "no_grammar" only if message type was converted from direct_grammar_search
        if not mode == "no_grammar":
            mode = "thinking_grammar_answer"

        return {"llm_response": thinking_grammar_response.output, "mode": mode}

    if router_agent_response.output.message_type == "casual_answer":
        casual_response = await system_agent.run(
            user_prompt=message.user_prompt,
            usage_limits=UsageLimits(request_limit=3),
            output_type=str,
            message_history=message_history[:-2],
        )
        local_logfire.info("System agent response: {response}", response=casual_response.output)

        with local_logfire.span("update_message_history"):
            user_message = ModelRequest(parts=[UserPromptPart(content=message.user_prompt)])
            model_response = ModelResponse(parts=[TextPart(content=casual_response.output)])

            # new_messages = casual_response.new_messages()
            new_messages = [user_message, model_response]

            background_tasks.add_task(update_message_history, session, message.user, new_messages)
            local_logfire.info(f"new_messages: {new_messages}")

        mode = "casual_answer"
        return {"llm_response": casual_response.output, "mode": mode}


    else:
        local_logfire.error(f"Unknown message type: {router_agent_response.output.message_type}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# @app.post("/invoke_test")
# async def without_llm(
#         message: TelegramMessage,
#         background_tasks: BackgroundTasks,
#         session: AsyncSession = Depends(get_db)
# ):
#     allowed_users = await get_user_ids(session)
#     if message.user.user_id not in allowed_users:
#         raise HTTPException(status_code=403,
#                             detail="User not registered")
#
#     grammar_entry = GrammarEntryV2(
#         grammar_name_kr="N + (이)야",
#         grammar_name_rus="«это…», «является…» (неофициально-невежливый стиль, панмаль)",
#         level=1,
#         related_grammars=["입니다/입니까", "**이에요 / 예요**"],
#         content="**Описание:** \n**이야** - это форма связки **이다** в неофициально-невежливом стиле. Используется при разговоре с близкими людьми, ровесниками или младшими, когда нет необходимости соблюдать вежливость. \n\n**Форма:** \n> с существительными, оканчивающимися на **согласную**: **N + 이야** \n> с существительными, оканчивающимися на **гласную**: **N + 야** \n\n**Примеры:**\n 내 친구는 의사**야**. Мой друг - врач. 이건 내 가방**이야**. Это моя сумка. 오늘은 내 생일**이야**. Сегодня мой день рождения. \n\n**Примечания:** \n1. Это **самая простая и невежливая форма**, не используется в официальных ситуациях, с малознакомыми людьми. \n2. Подходит только для неформального общения с очень хорошими друзьями или детьми. \n3. Это аналог форм **이에요 / 예요, 입니다/입니까** в неофициальном стиле."
#     )
#     mode = "single_grammar"
#     retrieved_grammars = [grammar_entry]
#     return {"llm_response": retrieved_grammars, "mode": mode}