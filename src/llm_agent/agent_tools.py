"""
Stores all necessary tools used by the agent(s).
"""

import logfire
from dotenv import load_dotenv
from pydantic_ai import RunContext
from qdrant_client.http.models import Prefetch, SparseVector, FusionQuery, Fusion

from src.config.settings import Config
from src.schemas.schemas import GrammarEntryV2, RetrievedGrammar, RouterAgentDeps, RetrievedDoc

load_dotenv()
config = Config()
logfire.configure(token=config.logfire_api_key)


async def retrieve_grammars_tool(
    context: RunContext[RouterAgentDeps], search_query: str, retrieve_top_k: int = 15
) -> list[GrammarEntryV2] | None:
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
        vector_query = await context.deps.openai_client.embeddings.create(model=config.embedding_model, input=search_query)
        sparse_vector_query = next(context.deps.sparse_embedding.query_embed(search_query))
        sparse_vector_query = SparseVector(**sparse_vector_query.as_object())

    assert len(vector_query.data) == 1, (
        f"Expected 1 embedding, got {len(vector_query.data)}, doc query: {search_query!r}"
    )

    vector_query = vector_query.data[0].embedding

    bm_threshold = 0
    vector_threshold = 0

    # Set up the Hybrid search prefetches
    bm_25_prefetch = Prefetch(
        query=sparse_vector_query,
        using=config.sparse_embedding_model,
        limit=retrieve_top_k,
        score_threshold=bm_threshold,
    )
    
    dense_prefetch = Prefetch(
        query=vector_query,
        using=config.embedding_model,
        limit=retrieve_top_k,
        score_threshold=vector_threshold,
    )

    # Use hybrid search with bm25 amd OpenAI embeddings with RRF
    # logfire.info(f"Trying to retrieve from {context.deps.qdrant_client.__dict__}")
    hits = context.deps.qdrant_client.query_points(
        collection_name=config.qdrant_collection_name_v2,
        prefetch=[bm_25_prefetch, dense_prefetch],
        query=FusionQuery(fusion=Fusion.RRF),
        with_payload=True,
    ).points

    logfire.info(f"Received {len(hits)} results from Qdrant.")

    # Convert to schema objects
    docs = [
        RetrievedGrammar(
            id=hit.id,
            content=GrammarEntryV2(**hit.payload),
            score=hit.score,
        )
        for hit in hits
    ]

    if not docs:
        logfire.info("No documents found.")
        return None

    #TODO Try only reranking if the number of retrieved docs > docs to rerank
    #
    # cross_input = []
    # for doc in docs:
    #     doc_data = " ".join([doc.content.grammar_name_kr, doc.content.grammar_name_rus])
    #     cross_input.append([search_query, doc_data])
    #
    # scores = context.deps.reranking_model.predict(cross_input)
    #
    # # Add cross-encoder scores to docs
    # for idx in range(len(scores)):
    #     docs[idx].cross_score = float(scores[idx])
    #     logfire.info(f"Document {idx} reranking: {docs[idx].score:.4f} -> {scores[idx]:.4f}")
    #
    # # Sort by cross-encoder score
    # reranked_docs = sorted(docs, key=lambda x: x.cross_score, reverse=True)
    #
    # logfire.info(f"Sorted docs: {reranked_docs}")
    #
    # result = [doc.content for doc in reranked_docs[:rerank_top_k]]
    result = [doc.content for doc in docs]
    return result


async def retrieve_docs_tool(
        context: RunContext[RouterAgentDeps],
        search_query: str,
        retrieve_top_k: int = 15,
        rerank_top_k: int = 10
) -> list[GrammarEntryV2] | None:
    """
    Инструмент для извлечения документов на основе запроса пользователя.
    A tool for extracting documents based on the user's query.

    Args:
        context: the call context
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        rerank_top_k: количество результатов ПОСЛЕ reranking-а
    """
    with logfire.span(f"Creating embedding for search_query = {search_query}"):
        vector_query = await context.deps.openai_client.embeddings.create(model=config.embedding_model,
                                                                          input=search_query)
        sparse_vector_query = next(context.deps.sparse_embedding.query_embed(search_query))
        sparse_vector_query = SparseVector(**sparse_vector_query.as_object())

    assert len(vector_query.data) == 1, (
        f"Expected 1 embedding, got {len(vector_query.data)}, doc query: {search_query!r}"
    )

    vector_query = vector_query.data[0].embedding

    bm_threshold = 0
    vector_threshold = 0

    # Set up the Hybrid search prefetches
    bm_25_prefetch = Prefetch(
        query=sparse_vector_query,
        using=config.sparse_embedding_model,
        limit=retrieve_top_k,
        score_threshold=bm_threshold,
    )

    dense_prefetch = Prefetch(
        query=vector_query,
        using=config.embedding_model,
        limit=retrieve_top_k,
        score_threshold=vector_threshold,
    )

    # Use hybrid search with bm25 amd OpenAI embeddings with RRF
    # logfire.info(f"Trying to retrieve from {context.deps.qdrant_client.__dict__}")
    hits = context.deps.qdrant_client.query_points(
        collection_name=config.qdrant_collection_name_rag,
        prefetch=[bm_25_prefetch, dense_prefetch],
        query=FusionQuery(fusion=Fusion.RRF),
        with_payload=True,
    ).points

    logfire.info(f"Received {len(hits)} results from Qdrant.")

    # Convert to schema objects
    docs = [
        RetrievedDoc(
            id=hit.id,
            content=hit.payload,
            score=hit.score,
        )
        for hit in hits
    ]

    if not docs:
        logfire.info("No documents found.")
        return None

    # TODO Try only reranking if the number of retrieved docs > docs to rerank
    #
    cross_input = []
    for doc in docs:
        doc_data = ". ".join([doc.content["topic"], doc.content["subtopic"], doc.content["content"]])
        cross_input.append([search_query, doc_data])

    scores = context.deps.reranking_model.predict(cross_input)

    # Add cross-encoder scores to docs
    for idx in range(len(scores)):
        docs[idx].cross_score = float(scores[idx])
        logfire.info(f"Document {idx} reranking: {docs[idx].score:.4f} -> {scores[idx]:.4f}")

    # Sort by cross-encoder score
    reranked_docs = sorted(docs, key=lambda x: x.cross_score, reverse=True)

    logfire.info(f"Sorted docs: {reranked_docs}")

    result = [doc.content["content"] for doc in reranked_docs[:rerank_top_k]]
    return result