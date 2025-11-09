from typing import List

import logfire
from dotenv import load_dotenv
from pydantic_ai.agent import  Agent
from qdrant_client.http.models import Prefetch, SparseVector, FusionQuery, Fusion

from src.config.settings import Config
from src.schemas.schemas import GrammarEntryV2, RetrievedGrammar, RouterAgentDeps, ThinkingGrammarAgentDeps

load_dotenv()
config = Config()

import asyncio  # Added for timing
from typing import List  # Added for output_type=List[int]


# Assuming other necessary imports are present
# (e.g., logfire, config, GrammarEntryV2, RouterAgentDeps, etc.)


async def hybrid_retrieve_grammars(
        deps: RouterAgentDeps,
        search_query: str,
        user_prompt: str,
        retrieve_top_k: int = 20,
        llm_filter: bool = True
) -> dict:
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.

    Args:
        deps: the call context's dependencies
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        user_prompt: User original prompt
        llm_filter: Whether to use llm filter or not

    Returns:
        A dictionary containing:
            - 'payload': list[GrammarEntryV2] | None (the original return value)
            - 'processing_times': dict with timings (in seconds) for major steps
    """

    # --- Setup Timings ---
    processing_times = {
        "embedding_generation_time": 0.0,
        "qdrant_query_time": 0.0,
        "qdrant_postprocessing_time": 0.0,
        "llm_filter_time": 0.0,
        "overall_time": 0.0
    }
    loop = asyncio.get_event_loop()

    # --- 1. Embedding Generation ---
    start_time = loop.time()
    with logfire.span("Creating embedding for search_query = {search_query}", search_query=search_query):
        vector_query = await deps.openai_client.embeddings.create(model=config.embedding_model, input=search_query)
        sparse_vector_query = next(deps.sparse_embedding.query_embed(search_query))
        sparse_vector_query = SparseVector(**sparse_vector_query.as_object())
    processing_times["embedding_generation_time"] = loop.time() - start_time

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

    # --- 2. Qdrant Query ---
    start_time = loop.time()
    with logfire.span(f"Querying Qdrant for search_query = {search_query}"):
        # Use hybrid search with bm25 amd OpenAI embeddings with RRF
        response = await deps.qdrant_client.query_points(
            collection_name=config.qdrant_collection_name_final,
            prefetch=[bm_25_prefetch, dense_prefetch],
            query=FusionQuery(fusion=Fusion.RRF),
            with_payload=True,
        )
        hits = response.points
    processing_times["qdrant_query_time"] = loop.time() - start_time

    # --- 3. Qdrant Post-processing ---
    start_time = loop.time()
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

    logfire.info(f"Retrieved docs: {docs}")
    processing_times["qdrant_postprocessing_time"] = loop.time() - start_time

    if not docs:
        logfire.info("No documents found.")
        # Modified return
        return {
            "payload": None,
            "processing_times": processing_times
        }

    else:
        result = [doc.content for doc in docs]

        if llm_filter:
            # --- 4. LLM Filtering ---
            start_time = loop.time()
            llm_filter_prompt = [f"USER_QUERY: '{user_prompt}'\n\nGRAMMAR LIST: "]

            for i, doc in enumerate(result):
                # ! For Version 1 grammars (full in json)
                llm_filter_prompt.append(f"{i}. {doc.grammar_name_kr} - {doc.grammar_name_rus}")

                # ! For Version 2 grammars (MD)
                # llm_filter_prompt.append(f"{i}. {doc}")

            llm_filter_agent = Agent(
                model="openai:gpt-4.1",
                instrument=True,
                output_type=List[int],
                instructions="""
                    You're a search filter in Korean grammar database. Select all relevant search results from the GRAMMAR LIST, 
                    based on the USER QUERY, and output their index only in a list. Focus on higher recall, if the number of potential 
                    results is more that 1, and higher precision if there is only 1 relevant result (i.e. it should be exactly what the 
                    user is looking for. If none are relevant, output an empty list

                    Example 1 - high recall:
                    ```
                    USER_QUERY: 'грамматика будущего времени в корейском языке'
                    GRAMMAR LIST: 
                    0. V/A + -(으)ㄹ 것이다 - будущее время
                    1. V + -겠- - будущее время (планы, намерения говорящего)
                    2. A/V + -(으)ㄹ 때, N + 때 - - «когда…», «во время…»
                    3. N + 에 - «в (какое-то время)»
                    4. V + -(으)ㄹ - определительная форма глагола в будущем времени
                    5. V/A + -(으)면서 - одновременность действий
                    6. V/A + -었-, -았-, -였- - суффикс прошедшего времени

                    OUTPUT: [0, 1, 4]
                    ```

                    Example 2 - higher precision
                    ```
                    USER_QUERY: 'грамматика 는 데'
                    GRAMMAR LIST:
                    0. N + 은/는 - выделительная частица
                    1. N + 하고 - «с» (совместное действие)
                    2. V + -는 동안(에) - «в течение…, пока…»
                    3. V/A + -(으)ㄴ/는데 - «а», «но», вводит контраст, предысторию или контекст
                    4. V + -는 것 - «делание», «то, что…», отглагольное существительное


                    OUTPUT: [3]
                    ```

                    Example 3 - high precision, but none relevant:
                    ```
                    USER_QUERY: 'объясни использование 아/어 보이다'
                    GRAMMAR LIST:
                    0. 보다 - «чем»
                    1. V + -(으)ㄹ까 보다 - «боюсь, что…», «волнуюсь, что…»
                    2. V + -아/어 있다 - состояние, возникшее в результате действия
                    3. V + -고 있다 - состояние одежды и внешнего вида
                    4. 와/과 - «с», совместное действие

                    OUTPUT: []
                    ```
                    """
            )

            llm_filter_response = await llm_filter_agent.run(user_prompt="\n\n".join(llm_filter_prompt))
            processing_times["llm_filter_time"] = loop.time() - start_time  # End timer for LLM
            processing_times["overall_time"] = sum(processing_times.values())

            filtered_doc_ids = llm_filter_response.output

            if filtered_doc_ids:
                filtered_docs = [result[i] for i in filtered_doc_ids]
                logfire.info(f"LLM filtered docs: {filtered_docs}")
                # Modified return
                return {
                    "retrieved_grammars": filtered_docs,
                    "processing_times": processing_times
                }

            else:
                # Modified return
                return {
                    "retrieved_grammars": [],
                    "processing_times": processing_times
                }
        else:
            # Modified return (no LLM filter)
            return {
                "retrieved_grammars": result[:5],
                "processing_times": processing_times
            }

async def keyword_retrieve_grammars(
        deps: RouterAgentDeps,
        search_query: str,
        user_prompt: str,
        retrieve_top_k: int = 15,
        llm_filter: bool = True
) -> dict:
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.

    Args:
        deps: the call context's dependencies
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        user_prompt: User original prompt
        llm_filter: Whether to use llm filter or not

    Returns:
        A dictionary containing:
            - 'payload': list[GrammarEntryV2] | None (the original return value)
            - 'processing_times': dict with timings (in seconds) for major steps
    """

    # --- Setup Timings ---
    processing_times = {
        "embedding_generation_time": 0.0,
        "qdrant_query_time": 0.0,
        "qdrant_postprocessing_time": 0.0,
        "llm_filter_time": 0.0,
        "overall_time": 0.0
    }
    loop = asyncio.get_event_loop()

    # --- 1. Embedding Generation ---
    start_time = loop.time()
    with logfire.span("Creating embedding for search_query = {search_query}", search_query=search_query):
        vector_query = await deps.openai_client.embeddings.create(model=config.embedding_model, input=search_query)
        sparse_vector_query = next(deps.sparse_embedding.query_embed(search_query))
        sparse_vector_query = SparseVector(**sparse_vector_query.as_object())
    processing_times["embedding_generation_time"] = loop.time() - start_time

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

    # --- 2. Qdrant Query ---
    start_time = loop.time()
    with logfire.span(f"Querying Qdrant for search_query = {search_query}"):
        # Use hybrid search with bm25 amd OpenAI embeddings with RRF
        response = await deps.qdrant_client.query_points(
            collection_name=config.qdrant_collection_name_final,
            prefetch=[bm_25_prefetch, dense_prefetch],
            query=FusionQuery(fusion=Fusion.RRF),
            with_payload=True,
        )
        hits = response.points
    processing_times["qdrant_query_time"] = loop.time() - start_time

    # --- 3. Qdrant Post-processing ---
    start_time = loop.time()
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

    logfire.info(f"Retrieved docs: {docs}")
    processing_times["qdrant_postprocessing_time"] = loop.time() - start_time

    if not docs:
        logfire.info("No documents found.")
        # Modified return
        return {
            "payload": None,
            "processing_times": processing_times
        }

    else:
        result = [doc.content for doc in docs]

        if llm_filter:
            # --- 4. LLM Filtering ---
            start_time = loop.time()
            llm_filter_prompt = [f"USER_QUERY: '{user_prompt}'\n\nGRAMMAR LIST: "]

            for i, doc in enumerate(result):
                # ! For Version 1 grammars (full in json)
                llm_filter_prompt.append(f"{i}. {doc.grammar_name_kr} - {doc.grammar_name_rus}")

                # ! For Version 2 grammars (MD)
                # llm_filter_prompt.append(f"{i}. {doc}")

            llm_filter_agent = Agent(
                model="openai:gpt-4.1",
                instrument=True,
                output_type=List[int],
                instructions="""
                    You're a search filter in Korean grammar database. Select all relevant search results from the GRAMMAR LIST, 
                    based on the USER QUERY, and output their index only in a list. Focus on higher recall, if the number of potential 
                    results is more that 1, and higher precision if there is only 1 relevant result (i.e. it should be exactly what the 
                    user is looking for. If none are relevant, output an empty list

                    Example 1 - high recall:
                    ```
                    USER_QUERY: 'грамматика будущего времени в корейском языке'
                    GRAMMAR LIST: 
                    0. V/A + -(으)ㄹ 것이다 - будущее время
                    1. V + -겠- - будущее время (планы, намерения говорящего)
                    2. A/V + -(으)ㄹ 때, N + 때 - - «когда…», «во время…»
                    3. N + 에 - «в (какое-то время)»
                    4. V + -(으)ㄹ - определительная форма глагола в будущем времени
                    5. V/A + -(으)면서 - одновременность действий
                    6. V/A + -었-, -았-, -였- - суффикс прошедшего времени

                    OUTPUT: [0, 1, 4]
                    ```

                    Example 2 - higher precision
                    ```
                    USER_QUERY: 'грамматика 는 데'
                    GRAMMAR LIST:
                    0. N + 은/는 - выделительная частица
                    1. N + 하고 - «с» (совместное действие)
                    2. V + -는 동안(에) - «в течение…, пока…»
                    3. V/A + -(으)ㄴ/는데 - «а», «но», вводит контраст, предысторию или контекст
                    4. V + -는 것 - «делание», «то, что…», отглагольное существительное


                    OUTPUT: [3]
                    ```

                    Example 3 - high precision, but none relevant:
                    ```
                    USER_QUERY: 'объясни использование 아/어 보이다'
                    GRAMMAR LIST:
                    0. 보다 - «чем»
                    1. V + -(으)ㄹ까 보다 - «боюсь, что…», «волнуюсь, что…»
                    2. V + -아/어 있다 - состояние, возникшее в результате действия
                    3. V + -고 있다 - состояние одежды и внешнего вида
                    4. 와/과 - «с», совместное действие

                    OUTPUT: []
                    ```
                    """
            )

            llm_filter_response = await llm_filter_agent.run(user_prompt="\n\n".join(llm_filter_prompt))
            processing_times["llm_filter_time"] = loop.time() - start_time  # End timer for LLM
            processing_times["overall_time"] = sum(processing_times.values())

            filtered_doc_ids = llm_filter_response.output

            if filtered_doc_ids:
                filtered_docs = [result[i] for i in filtered_doc_ids]
                logfire.info(f"LLM filtered docs: {filtered_docs}")
                # Modified return
                return {
                    "retrieved_grammars": filtered_docs,
                    "processing_times": processing_times
                }

            else:
                # Modified return
                return {
                    "retrieved_grammars": [],
                    "processing_times": processing_times
                }
        else:
            # Modified return (no LLM filter)
            return {
                "retrieved_grammars": result[:5],
                "processing_times": processing_times
            }