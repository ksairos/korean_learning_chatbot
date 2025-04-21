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

router_agent = Agent(
    model="openai:gpt-4o-mini",
    instrument=True,
    output_type=RouterAgentResult,
    instructions=prompts.router_prompt_v2
)


@router_agent.tool
async def retrieve_docs(context: RunContext[RouterAgentDeps], search_query: str):
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    Args:
        context: the call context
        search_query: запрос для поиска
    """
    docs = await retrieve_docs_tool(context, search_query, 5)
    if docs:
        logfire.info(f"Retrieved docs: {docs}")
        return docs
    return "Нет подходящих грамматик"
        

@router_agent.tool
async def retrieve_single_grammar(context: RunContext[RouterAgentDeps], search_query: str):
    """
        Инструмент для извлечения ОДНОЙ грамматической конструкции на основе запроса пользователя.
        Args:
            context: the call context
            search_query: запрос для поиска
        """
    docs = await retrieve_docs_tool(context, search_query, 1)
    if docs:
        doc = docs[0]
        logfire.info(f"Retrieved doc: {doc}")

        return grammar_entry_to_markdown(doc.content)
    
    return "Нет подходящих грамматик"



@router_agent.tool_plain
async def translation_agent_call(user_prompt: str):
    """
    Инструмент для перевода текста с русского на корейский и наоборот

    Args:
        user_prompt: запрос для перевода
    """
    r = await translation_agent.run(user_prompt, output_type=TranslationAgentResult)
    return r.output.translation


translation_agent = Agent(
    "openai:gpt-4.5-preview",
    instrument=True,
    output_type=TranslationAgentResult,
    system_prompt=(
        """
        Вы — профессиональный многоязычный переводчик и языковой эксперт. Переведите данное сообщение пользователя, 
        точно передавая контекст, грамматику и тон. Если сообщение на русском языке, переведите его на корейский, 
        и наоборот. Не используйте другие языки, даже если об этом попросят. Тщательно проверяйте используемую лексику 
        и грамматику: грамматические конструкции должны быть точными, а лексика — звучать естественно.
        """
    )
)
