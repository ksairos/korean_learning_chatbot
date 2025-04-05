import logfire

from dotenv import load_dotenv
from qdrant_client.http.models import SparseVector, Prefetch

from src.config import prompts
from src.config.settings import Config

from pydantic_ai import Agent, RunContext

from src.schemas.schemas import RetrievedDocs, RetrieverDeps

load_dotenv()

config = Config()

logfire.configure(token=config.logfire_api_key)

agent = Agent(
    "openai:gpt-4o-mini",
    instrument=True,
    system_prompt=prompts.prompts.answer_generation,
    retries=2,
)

@agent.tool
async def retrieve(context: RunContext[RetrieverDeps], search_query: str) -> str:
    """Retrieve documentation sections based on a search query.

    Args:
        context: The call context.
        search_query: The search query.
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
    print(f"Trying to retrieve from {context.deps.qdrant_client.__dict__}")
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
            content=hit.payload["description"],
            metadata={k: v for k, v in hit.payload.items() if k != "content"},
            score=hit.score,
        ) for hit in hits
    ]

    return '\n\n'.join(
        f"{doc.metadata}" for doc in docs
    )









