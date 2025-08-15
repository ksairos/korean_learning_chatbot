"""
Stores all necessary tools used by the agent(s).
"""
from typing import List, Literal

import logfire
from dotenv import load_dotenv
from pydantic_ai import RunContext
from pydantic_ai.agent import  Agent
from qdrant_client.http.models import Prefetch, SparseVector, FusionQuery, Fusion

from src.config.settings import Config
from src.schemas.schemas import GrammarEntryV2, RetrievedGrammar, RouterAgentDeps, RetrievedDoc

load_dotenv()
config = Config()

async def retrieve_grammars_tool(
        deps: RouterAgentDeps,
        search_query: str,
        retrieve_top_k: int = 15
) -> list[GrammarEntryV2] | None:
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.

    Args:
        deps: the call context's dependencies
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        rerank_top_k: количество результатов ПОСЛЕ reranking-а
    """

    with logfire.span("Creating embedding for search_query = {search_query}", search_query=search_query):
        vector_query = await deps.openai_client.embeddings.create(model=config.embedding_model, input=search_query)
        sparse_vector_query = next(deps.sparse_embedding.query_embed(search_query))
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
    hits = deps.qdrant_client.query_points(
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

    else:
        result = [doc.content for doc in docs]

        llm_filter_prompt = [f"USER_QUERY: '{search_query}'\n\nGRAMMAR LIST: "]

        for i, doc in enumerate(result):
            # ! For Version 1 grammars (full in json)
            llm_filter_prompt.append(f"{i}. {doc.grammar_name_kr} - {doc.grammar_name_rus}")

            # ! For Version 2 grammars (MD)
            # llm_filter_prompt.append(f"{i}. {doc}")

        llm_filter_agent = Agent(
            model="openai:gpt-4o",
            instrument=True,
            output_type=List[int],
            instructions="""
                Based on the USER QUERY select appropriate search results from the GRAMMAR LIST, and output their index only
            """
        )

        llm_filter_response = await llm_filter_agent.run(user_prompt="\n\n".join(llm_filter_prompt))
        filtered_doc_ids = llm_filter_response.output
        filtered_docs = [result[i] for i in filtered_doc_ids]

        logfire.info(f"LLM filtered docs: {filtered_docs}")
        return filtered_docs


async def retrieve_docs_tool(
        deps: RouterAgentDeps,
        search_query: str,
        retrieve_top_k: int = 15,
        rerank_top_k: int = 3,
        search_strategy: Literal["bm25", "dense", "hybrid"] = "hybrid",
        rerank_strategy: Literal["cross", "colbert", "none"] = "cross",
) -> list[RetrievedDoc | None]:
    """
    Инструмент для извлечения документов на основе запроса пользователя.
    A tool for extracting documents based on the user's query.

    Args:
        deps: the call dependencies
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        rerank_top_k: количество результатов ПОСЛЕ reranking-а
        search_strategy: стратегия поиска
        rerank_strategy: стратегия для reranking-а
    """

    bm_threshold = 0
    vector_threshold = 0

    local_logfire = logfire.with_tags(search_strategy, rerank_strategy, "RETRIEVER")

    with local_logfire.span(f"Embedding for search_query = {search_query}"):

        if search_strategy == "dense" or search_strategy == "hybrid":
            vector_query = await deps.openai_client.embeddings.create(
                model=config.embedding_model,
                input=search_query)
            vector_query = vector_query.data[0].embedding

            dense_prefetch = Prefetch(
                query=vector_query,
                using=config.embedding_model,
                limit=retrieve_top_k,
                score_threshold=vector_threshold,
            )

        if search_strategy == "bm25" or search_strategy == "hybrid":
            sparse_vector_query = next(deps.sparse_embedding.query_embed(search_query))
            sparse_vector_query = SparseVector(**sparse_vector_query.as_object())

            bm_25_prefetch = Prefetch(
                query=sparse_vector_query,
                using=config.sparse_embedding_model,
                limit=retrieve_top_k,
                score_threshold=bm_threshold,
            )

        if search_strategy == "hybrid" and rerank_strategy == "colbert":
            late_vector_query = next(deps.late_interaction_model.query_embed(search_query))

        local_logfire.info(f"Query embedded with OpenAI and sparse embeddings")


    # Use hybrid search with bm25 amd OpenAI embeddings with RRF
    # local_logfire.info(f"Trying to retrieve from {deps.qdrant_client.__dict__}")

    with local_logfire.span("Retrieving from Qdrant"):

        if search_strategy == "hybrid":
            if rerank_strategy == "cross":
                hits = deps.qdrant_client.query_points(
                    collection_name=config.qdrant_collection_name_rag,
                    prefetch=[bm_25_prefetch, dense_prefetch],
                    query=FusionQuery(fusion=Fusion.RRF),
                    with_payload=True,
                ).points
                local_logfire.info(f"Received {len(hits)} results from Qdrant.")

            elif rerank_strategy == "colbert":
                hits = deps.qdrant_client.query_points(
                    collection_name=config.qdrant_collection_name_rag_colbert,
                    prefetch=[bm_25_prefetch, dense_prefetch],
                    query=late_vector_query,
                    using=config.late_interaction_model,
                    limit=rerank_top_k,
                    with_payload=True,
                ).points

        elif search_strategy == "bm25":
            hits = deps.qdrant_client.query_points(
                collection_name=config.qdrant_collection_name_rag,
                prefetch=[bm_25_prefetch],
                query=sparse_vector_query,
                with_payload=True,
            ).points

        elif search_strategy == "dense":
            hits = deps.qdrant_client.query_points(
                collection_name=config.qdrant_collection_name_rag,
                prefetch=[dense_prefetch],
                query=vector_query,
                with_payload=True,
            ).points


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
        local_logfire.info("No documents found.")
        return []

    if rerank_strategy == "cross":

        cross_input = []
        for doc in docs:
            doc_data = doc.content["content"]
            cross_input.append([search_query, doc_data])

        with local_logfire.span("Reranking with cross-encoder"):
            scores = deps.reranking_model.predict(cross_input)

        # Add cross-encoder scores to docs
        for idx in range(len(scores)):
            docs[idx].cross_score = float(scores[idx])

        # Sort by cross-encoder score
        reranked_docs = sorted(docs, key=lambda x: x.cross_score, reverse=True)

        local_logfire.info(f"Original docs: {docs}")
        local_logfire.info(f"Sorted docs: {reranked_docs}")

        try:
            result = reranked_docs[:rerank_top_k]
            return result

        except:
            return reranked_docs

    else:
        return docs