import logfire

from dotenv import load_dotenv
from qdrant_client.http.models import SparseVector, Prefetch

from src.config import prompts
from src.config.settings import Config

from pydantic_ai import Agent, RunContext

from src.llm_agent.agent_tools import retrieve_docs_tool
from src.schemas.schemas import GrammarEntry, RetrievedDocs, RetrieverDeps

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
async def retrieve_docs(context: RunContext[RetrieverDeps], search_query: str):
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.

    Args:
        context: the call context
        search_query: запрос для поиска
    """
    return await retrieve_docs_tool(context, search_query)