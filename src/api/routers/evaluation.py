import logfire
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai.usage import UsageLimits

from src.api.evaluation.eval_retrieve_grammars_tool import eval_retrieve_grammars_tool
from src.api.evaluation.strategies import STRATEGY_MAP, RagEvaluationStrategy
from src.config.settings import Config
from src.db.crud import get_user_ids
from src.db.database import get_db
from src.llm_agent.agent import query_rewriter_agent
from src.llm_agent.agent_tools import retrieve_grammars_tool
from src.schemas.schemas import RouterAgentDeps, TelegramMessage

router = APIRouter(prefix="/evaluate", tags=["evaluation"])

config = Config()

local_logfire = logfire.with_tags("evaluation")

async def get_evaluation_deps(session: AsyncSession):
    from src.api.main import openai_client, qdrant_client, sparse_embedding, late_interaction_model
    
    return RouterAgentDeps(
        openai_client=openai_client,
        qdrant_client=qdrant_client,
        sparse_embedding=sparse_embedding,
        late_interaction_model=late_interaction_model,
        session=session,
    )


async def verify_user_access(user_id: int, session: AsyncSession) -> None:
    allowed_users = await get_user_ids(session)
    if user_id not in allowed_users:
        raise HTTPException(status_code=403, detail="User not registered")


async def _run_evaluation_strategy(
        strategy_key: str,
        message: TelegramMessage,
        retrieve_top_k: int,
        rerank_top_k: int,
        session: AsyncSession):
    """Common evaluation logic for all strategies"""
    # IMPORTANT: Comment if issues with SQL Alchemy timeouts during evaluations
    await verify_user_access(message.user.user_id, session)
    
    deps = await get_evaluation_deps(session)

    strategy: RagEvaluationStrategy = STRATEGY_MAP[strategy_key]
    strategy.retrieve_top_k = retrieve_top_k
    strategy.rerank_top_k = rerank_top_k

    local_logfire.info(f"Running evaluation strategy: {strategy.__dict__}")

    return await strategy.evaluate(message, deps)


@router.post("/test1")
async def evaluate_rag_cross_encoder(
        message: TelegramMessage,
        retrieve_top_k: int,
        rerank_top_k: int,
        session: AsyncSession = Depends(get_db),
):
    return await _run_evaluation_strategy("test1", message, retrieve_top_k, rerank_top_k, session)


@router.post("/test2")
async def evaluate_rag_colbert(
        message: TelegramMessage,
        retrieve_top_k: int,
        rerank_top_k: int,
        session: AsyncSession = Depends(get_db),
):
    return await _run_evaluation_strategy("test2", message, retrieve_top_k, rerank_top_k, session)


@router.post("/test3")
async def evaluate_rag_no_rerank(
        message: TelegramMessage,
        retrieve_top_k: int,
        rerank_top_k: int,
        session: AsyncSession = Depends(get_db),
):
    return await _run_evaluation_strategy("test3", message, retrieve_top_k, rerank_top_k, session)


@router.post("/test4")
async def evaluate_rag_no_rerank(
        message: TelegramMessage,
        retrieve_top_k: int,
        rerank_top_k: int,
        session: AsyncSession = Depends(get_db),
):
    return await _run_evaluation_strategy("test4", message, retrieve_top_k, rerank_top_k, session)

@router.post("/test5")
async def evaluate_rag_colbert(
        message: TelegramMessage,
        retrieve_top_k: int,
        rerank_top_k: int,
        session: AsyncSession = Depends(get_db),
):
    return await _run_evaluation_strategy("test5", message, retrieve_top_k, rerank_top_k, session)


@router.post("/direct_search")
async def direct_search_eval(user_prompt: str, strategy: str):
    with local_logfire.span(f"Strategy: {strategy}"):
        local_logfire.info(f'Query: {user_prompt}')

        query = user_prompt

        deps = await get_evaluation_deps(AsyncSession())

        if not strategy == "no_rewriter":
            query_rewriter_response = await query_rewriter_agent.run(
                user_prompt=user_prompt,
                usage_limits=UsageLimits(request_limit=1),
            )
            local_logfire.info(f"Rewritten query: {query_rewriter_response.output}")
            query = query_rewriter_response.output

        retrieved_grammars = await eval_retrieve_grammars_tool(deps, query, user_prompt)
        return retrieved_grammars