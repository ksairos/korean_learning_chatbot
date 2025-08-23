from typing import Dict, Any, List
import logfire
from pydantic_ai.usage import UsageLimits
from pydantic_ai import Agent

from src.llm_agent.agent import hyde_agent, thinking_grammar_agent
from src.llm_agent.agent_tools import retrieve_docs_tool
from src.schemas.schemas import RouterAgentDeps, TelegramMessage, RetrievedDoc


class RagEvaluationStrategy:
    """Base class for RAG evaluation strategies"""
    
    def __init__(
            self,
            search_strategy: str = "hybrid",
            rerank_strategy: str = "colbert",
            retrieve_top_k: int = 50,
            rerank_top_k: int = 5
    ):
        self.search_strategy = search_strategy
        self.rerank_strategy = rerank_strategy
        self.retrieve_top_k = retrieve_top_k
        self.rerank_top_k = rerank_top_k
    
    async def evaluate(self, message: TelegramMessage, deps: RouterAgentDeps) -> Dict[str, Any]:
        """Execute the evaluation strategy"""
        local_logfire = logfire.with_tags(
            str(message.user.user_id), 
            "evaluation",
            self.search_strategy,
            self.rerank_strategy
        )
        
        local_logfire.info(f'User message: "{message}"')

        hyde_response = await hyde_agent.run(user_prompt=message.user_prompt)
        
        with local_logfire.span("document_retrieval"):
            retrieved_docs: List[RetrievedDoc | None] = await retrieve_docs_tool(
                deps=deps,
                search_query=hyde_response.output,
                search_strategy=self.search_strategy,
                rerank_strategy=self.rerank_strategy,
                rerank_top_k=self.rerank_top_k,
                retrieve_top_k=self.retrieve_top_k
            )
        
        # docs = [doc.content["content"] for doc in retrieved_docs if doc]
        # local_logfire.info(f"Retrieved {len(docs)} docs")

        llm_filter_prompt = [f"USER_QUERY: '{message.user_prompt}'\n\nCONTEXT: "]

        for i, doc in enumerate(retrieved_docs):
            llm_filter_prompt.append(f"{i}. {doc.content["content"]}")

        local_logfire.info(f"LLM Filter Prompt{llm_filter_prompt}")

        llm_filter_agent = Agent(
            model="gpt-5",
            instrument=True,
            output_type=List[int],
            instructions=
            """Analyze the USER QUERY and select appropriate search results from the CONTEXT,
            that can directly or indirectly be used to respond to the USER QUERY. 
            Output their index, sorted by the relevance to the USER QUERY"""
        )

        llm_filter_response = await llm_filter_agent.run(user_prompt="\n\n".join(llm_filter_prompt))
        filtered_doc_ids = llm_filter_response.output
        filtered_docs = [retrieved_docs[i] for i in filtered_doc_ids]

        logfire.info(f"LLM filtered docs: {filtered_docs}")

        if len(filtered_docs) > 5:
            filtered_docs = filtered_docs[:5]

        thinking_grammar_response = await thinking_grammar_agent.run(
            user_prompt=message.user_prompt,
            deps=filtered_docs,
            usage_limits=UsageLimits(request_limit=5),
        )

        local_logfire.info("RAG Pipeline completed",
                         response_length=len(thinking_grammar_response.output))
        
        return {
            "llm_response": thinking_grammar_response.output,
            "retrieved_docs": filtered_docs,
        }

# retrieve_top_k=10
# rerank_top_k=3

retrieve_top_k=50
rerank_top_k=5

# Pre-configured strategies
CROSS_ENCODER_STRATEGY = RagEvaluationStrategy(
    search_strategy="hybrid", 
    rerank_strategy="cross",
    retrieve_top_k=retrieve_top_k,
    rerank_top_k=rerank_top_k
)

COLBERT_STRATEGY = RagEvaluationStrategy(
    search_strategy="hybrid", 
    rerank_strategy="colbert",
    retrieve_top_k=retrieve_top_k,
    rerank_top_k=rerank_top_k
)

NO_RERANK_HYBRID_STRATEGY = RagEvaluationStrategy(
    search_strategy="hybrid", 
    rerank_strategy="none",
    retrieve_top_k=retrieve_top_k,
    rerank_top_k=rerank_top_k
)

NO_RERANK_DENSE_STRATEGY = RagEvaluationStrategy(
    search_strategy="dense",
    rerank_strategy="none",
    retrieve_top_k=retrieve_top_k,
    rerank_top_k=rerank_top_k
)

NO_RERANK_BM25_STRATEGY = RagEvaluationStrategy(
    search_strategy="bm25",
    rerank_strategy="none",
    retrieve_top_k=retrieve_top_k,
    rerank_top_k=rerank_top_k
)


STRATEGY_MAP = {
    "test1": CROSS_ENCODER_STRATEGY,
    "test2": COLBERT_STRATEGY, 
    "test3": NO_RERANK_HYBRID_STRATEGY,
    "test4": NO_RERANK_DENSE_STRATEGY,
    "test5": NO_RERANK_BM25_STRATEGY
}