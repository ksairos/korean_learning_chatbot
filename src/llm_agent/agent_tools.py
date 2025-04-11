"""
Stores all necessary tools used by the agent(s).
"""

import logfire

from dotenv import load_dotenv
from qdrant_client.http.models import SparseVector, Prefetch

from src.config.settings import Config

from pydantic_ai import RunContext

from src.schemas.schemas import GrammarEntry, RetrievedDocs, RouterAgentDeps

load_dotenv()
config = Config()
logfire.configure(token=config.logfire_api_key)


async def retrieve_docs_tool(context: RunContext[RouterAgentDeps], search_query: str):
    """Инструмент для извлечения грамматических конструкций на основе запроса пользователя.

    Args:
        context: the call context
        search_query: запрос для поиска
    """
    with logfire.span(
            f"Creating embedding for search_query = {search_query}"
    ):
        vector_query = await context.deps.openai_client.embeddings.create(
            model=config.embedding_model,
            input=search_query
        )
        sparse_vector_query = next(context.deps.sparse_embedding.query_embed(search_query))
        sparse_vector_query = SparseVector(**sparse_vector_query.as_object())

    assert len(vector_query.data) == 1, (
        f'Expected 1 embedding, got {len(vector_query.data)}, doc query: {search_query!r}'
    )

    vector_query = vector_query.data[0].embedding

    top_k = 5
    threshold = 0

    bm_25_prefetch = [
        Prefetch(
            query=sparse_vector_query,
            using=config.sparse_embedding_model,
            limit=top_k,
            score_threshold=threshold
        )
    ]

    logfire.info(f"Prefetch configured for sparse vector")

    logfire.info(f"Trying to retrieve from {context.deps.qdrant_client.__dict__}")
    hits = context.deps.qdrant_client.query_points(
        collection_name=config.qdrant_collection_name,
        using=config.embedding_model,
        query=vector_query,
        limit=top_k,
        prefetch=bm_25_prefetch,
        score_threshold=threshold,
        with_payload=True
    ).points

    # hits = hits_response.points
    logfire.info(f"Received {len(hits)} results from Qdrant.")

    # Convert to schema objects
    docs = [
        RetrievedDocs(
            content=GrammarEntry(**hit.payload),
            score=hit.score,
        ) for hit in hits
    ]
    
    if not docs:
        logfire.info("No documents found.")
        return "Нет подходящих грамматик"
    
    else:

        formatted_docs = "Подходящие грамматики:\n\n" + '\n\n'.join(
            f"{doc.content.model_dump_json(indent=2)}" for doc in docs
        )

        logfire.info(f"Formatted docks: {formatted_docs}")

        return formatted_docs