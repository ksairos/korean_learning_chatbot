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
        retrieve_top_k: int = 50,
        rerank_top_k: int = 5,
        search_strategy: Literal["bm25", "dense", "hybrid"] = "hybrid",
        rerank_strategy: Literal["cross", "colbert", "none"] = "colbert",
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

            local_logfire.info(f"Query embedded with sparse embeddings")

            bm_25_prefetch = Prefetch(
                query=sparse_vector_query,
                using=config.sparse_embedding_model,
                limit=retrieve_top_k,
                score_threshold=bm_threshold,
            )

        if rerank_strategy == "colbert":
            late_vector_query = next(deps.late_interaction_model.query_embed(search_query))
            local_logfire.info(f"Query embedded with ColBERT")


    # Use hybrid search with bm25 amd OpenAI embeddings with RRF
    # local_logfire.info(f"Trying to retrieve from {deps.qdrant_client.__dict__}")

    with local_logfire.span(f"qdrant_retrieval_{search_strategy}_{rerank_strategy}"):

        if search_strategy == "hybrid":
            if rerank_strategy == "cross" or rerank_strategy == "none":
                hits = deps.qdrant_client.query_points(
                    collection_name=config.qdrant_collection_name_rag,
                    prefetch=[bm_25_prefetch, dense_prefetch],
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=retrieve_top_k,
                    with_payload=True,
                ).points
                local_logfire.info(f"Received {len(hits)} results from Qdrant.")

            elif rerank_strategy == "colbert":
                hits = deps.qdrant_client.query_points(
                    collection_name=config.qdrant_collection_name_rag,
                    prefetch=[bm_25_prefetch, dense_prefetch],
                    query=late_vector_query,
                    using=config.late_interaction_model,
                    limit=rerank_top_k,
                    with_payload=True,
                ).points
                local_logfire.info(f"Received {len(hits)} results from Qdrant.")

        elif search_strategy == "bm25" and rerank_strategy == "none":
            hits = deps.qdrant_client.query_points(
                collection_name=config.qdrant_collection_name_rag,
                query=sparse_vector_query,
                using=config.sparse_embedding_model,
                with_payload=True,
                limit=retrieve_top_k,
            ).points
            local_logfire.info(f"Received {len(hits)} results from Qdrant.")

        elif search_strategy == "dense" and rerank_strategy == "none":
            hits = deps.qdrant_client.query_points(
                collection_name=config.qdrant_collection_name_rag,
                using=config.embedding_model,
                query=vector_query,
                with_payload=True,
                limit=retrieve_top_k,
            ).points
            local_logfire.info(f"Received {len(hits)} results from Qdrant.")

        else:
            local_logfire.error(f"Unsupported search strategy <{search_strategy}> or Rerank strategy <{rerank_strategy}>")


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

        local_logfire.info(f"Original docs: {docs}")

        docs_content = []
        for doc in docs:
            doc_data = doc.content["content"]
            docs_content.append(doc_data)

        with local_logfire.span("Reranking with cross-encoder"):
            new_scores = deps.reranking_model.rerank(search_query, docs_content)
            ranking = [(i, score) for i, score in enumerate(new_scores)]
            local_logfire.info(f"Rankings: {ranking}")

            combined = zip(docs, ranking)
            sorted_combined = sorted(combined, key=lambda item: item[1][1], reverse=True)

            reranked_docs: List[RetrievedDoc] = []
            for doc, (rank, score) in sorted_combined:
                doc.cross_score = score
                reranked_docs.append(doc)


        local_logfire.info(f"Cross Encoder Sorted docs: {reranked_docs}")

        try:
            result = reranked_docs[:rerank_top_k]
            return result

        except:
            return reranked_docs

    if rerank_strategy == "colbert":
        local_logfire.info(f"Late Interaction Reranked docs: {docs}")
        return docs

    else:

        local_logfire.info(f"Docs without reranking: {docs}")
        return docs[:rerank_top_k]

