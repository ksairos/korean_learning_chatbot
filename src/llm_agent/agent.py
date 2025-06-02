import logfire

from dotenv import load_dotenv

from src.config.prompts import prompts
from src.config.settings import Config

from pydantic_ai import Agent, RunContext


from src.llm_agent.agent_tools import retrieve_docs_tool
from src.llm_agent.utils.json_to_telegram_md import grammar_entry_to_markdown
from src.schemas.schemas import RouterAgentDeps, TranslationAgentResult, RouterAgentResult

load_dotenv()

config = Config()
logfire.configure(token=config.logfire_api_key)

#INFO Modify to change the bot language
language = "ru"
if language == "ru":
    router_prompt = prompts.router_prompt_v2_ru
    translator_prompt = prompts.translator_prompt_ru
else:
    router_prompt = prompts.router_prompt_v2_en
    translator_prompt = prompts.translator_prompt_en


router_agent = Agent(
    model="openai:gpt-4o-mini",
    instrument=True,
    output_type=RouterAgentResult,
    instructions=router_prompt
)


@router_agent.tool
async def retrieve_docs(context: RunContext[RouterAgentDeps], search_query: str):
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.
    Args:
        context: the call context
        search_query: запрос для поиска
    """
    docs = await retrieve_docs_tool(context, search_query, 5)
    if docs:
        formatted_docs = [grammar_entry_to_markdown(doc.content) for doc in docs]
        logfire.info(f"Retrieved docs: {formatted_docs}")
        return formatted_docs
    return "Нет подходящих грамматик"

@router_agent.tool
async def retrieve_single_doc(context: RunContext[RouterAgentDeps], search_query: str):
    """
    Инструмент для поиска грамматической конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.
    Args:
        context: the call context
        search_query: запрос для поиска
    """
    pass


# @router_agent.tool
# async def retrieve_single_grammar(context: RunContext[RouterAgentDeps], search_query: str):
#     """
#         Инструмент для извлечения ОДНОЙ грамматической конструкции на основе запроса пользователя.
#         A tool for extracting a SINGLE grammatical construction based on the user's query.
#         Args:
#             context: the call context
#             search_query: запрос для поиска
#         """
#     docs = await retrieve_docs_tool(context, search_query, 1)
#     if docs:
#         doc = docs[0]
#         logfire.info(f"Retrieved doc: {doc}")

#         return grammar_entry_to_markdown(doc.content)
    
#     return "Нет подходящих грамматик"



@router_agent.tool_plain
async def translation_agent_call(user_prompt: str):
    """
    Инструмент для перевода текста с русского на корейский и наоборот.
    A tool for translating text from Russian to Korean and vice versa.
    Args:
        user_prompt: запрос для перевода
    """
    r = await translation_agent.run(user_prompt, output_type=TranslationAgentResult)
    return r.output.translation


translation_agent = Agent(
    "openai:gpt-4.5-preview",
    instrument=True,
    output_type=TranslationAgentResult,
    instructions=translator_prompt
)
