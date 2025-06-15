"""
The older version of the functions, that was using Multi-Stage Query search
Might be useful for thinking_grammar_answer
It was also using the v0-ai-generated data with JSON version of grammar entries
"""

import logfire
from dotenv import load_dotenv
from pydantic_ai import RunContext
from qdrant_client.http.models import Prefetch, SparseVector

from src.config.settings import Config
from src.schemas.schemas import GrammarEntryV2, RetrievedDoc, RouterAgentDeps

load_dotenv()
config = Config()
logfire.configure(token=config.logfire_api_key)


async def retrieve_docs_tool(
    context: RunContext[RouterAgentDeps], search_query: str, retrieve_top_k: int = 10, rerank_top_k: int = 4
) -> list[str] | None:
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.

    Args:
        context: the call context
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        rerank_top_k: количество результатов ПОСЛЕ reranking-а
    """
    with logfire.span(f"Creating embedding for search_query = {search_query}"):
        vector_query = await context.deps.openai_client.embeddings.create(
            model=config.embedding_model, input=search_query
        )
        sparse_vector_query = next(
            context.deps.sparse_embedding.query_embed(search_query)
        )
        sparse_vector_query = SparseVector(**sparse_vector_query.as_object())

    assert len(vector_query.data) == 1, (
        f"Expected 1 embedding, got {len(vector_query.data)}, doc query: {search_query!r}"
    )

    vector_query = vector_query.data[0].embedding

    bm_threshold = 0
    vector_threshold = 0

    # Retrieve top_k * 3 results using bm25 to then search from using semantic
    bm_25_prefetch = [
        Prefetch(
            query=sparse_vector_query,
            using=config.sparse_embedding_model,
            limit=retrieve_top_k * 3,
            score_threshold=bm_threshold,
        )
    ]

    # logfire.info("Prefetch configured for sparse vector")

    # logfire.info(f"Trying to retrieve from {context.deps.qdrant_client.__dict__}")
    hits = context.deps.qdrant_client.query_points(
        collection_name=config.qdrant_collection_name_v2,
        using=config.embedding_model,
        query=vector_query,
        limit=retrieve_top_k,
        prefetch=bm_25_prefetch,
        score_threshold=vector_threshold,
        with_payload=True,
    ).points

    # hits = hits_response.points
    logfire.info(f"Received {len(hits)} results from Qdrant.")

    # Convert to schema objects
    docs = [
        RetrievedDoc(
            content=GrammarEntryV2(**hit.payload),
            score=hit.score,
        )
        for hit in hits
    ]

    if not docs:
        logfire.info("No documents found.")
        return None

    #TODO Try only reranking if the number of retrieved docs > docs to rerank
    cross_input = []
    for doc in docs:
        #! For Version 1 grammars (full in json)
        # doc_data = " ".join([doc.content.grammar_name_kr, doc.content.grammar_name_rus])
        # cross_input.append([search_query, doc_data])
        cross_input.append([search_query, doc.content.grammar_name])
    logfire.info(f"Cross input: {cross_input}")
    scores = context.deps.reranking_model.predict(cross_input)

    # Add cross-encoder scores to docs
    for idx in range(len(scores)):
        docs[idx].cross_score = float(scores[idx])
        logfire.info(
            f"Document {idx} reranking: {docs[idx].score:.4f} -> {scores[idx]:.4f}"
        )

    # Sort by cross-encoder score
    reranked_docs = sorted(docs, key=lambda x: x.cross_score, reverse=True)

    # formatted_docs = "Подходящие грамматики:\n\n" + '\n\n'.join(
    #     f"{doc.content.model_dump_json(indent=2)}" for doc in sorted_docs
    # )
    
    logfire.info(f"Sorted docs: {reranked_docs}")

    result = [doc.content.content for doc in reranked_docs[:rerank_top_k]]
    return result