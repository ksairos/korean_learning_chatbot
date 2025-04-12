import logfire

from dotenv import load_dotenv
from qdrant_client.http.models import SparseVector, Prefetch

from src.config.prompts import prompts
from src.config.settings import Config

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits


from src.llm_agent.agent_tools import retrieve_docs_tool
from src.schemas.schemas import RouterAgentDeps, TranslationAgentResult, RouterAgentResult

load_dotenv()

config = Config()

logfire.configure(token=config.logfire_api_key)

router_agent = Agent(
    model="openai:gpt-4o-mini",
    instrument=True,
    result_type=RouterAgentResult,
    system_prompt=(
        prompts.router_prompt_v2
    )
)

# @router_agent.tool
# async def rewrite_query(context: RunContext[RouterAgentDeps], search_query: str):
#     """
#     Инструмент для улучшения запроса для поиска
#
#     Args:
#         context: the call context
#         search_query: запрос который нужно переписать
#     """
#     return await rewrite_query_tool(context, search_query)


@router_agent.tool
async def retrieve_docs(context: RunContext[RouterAgentDeps], search_query: str):
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    Args:
        context: the call context
        search_query: запрос для поиска
    """
    return await retrieve_docs_tool(context, search_query, 5)

@router_agent.tool
async def retrieve_single_grammar(context: RunContext[RouterAgentDeps], search_query: str):
    """
        Инструмент для извлечения ОДНОЙ грамматической конструкции на основе запроса пользователя.
        Args:
            context: the call context
            search_query: запрос для поиска
        """
    return await retrieve_docs_tool(context, search_query, 2)



@router_agent.tool_plain
async def translation_agent_call(user_prompt: str):
    """
    Инструмент для перевода текста с русского на корейский и наоборот

    Args:
        user_prompt: запрос для перевода
    """
    r = await translation_agent.run(user_prompt, result_type=TranslationAgentResult)
    return r.data.translation


translation_agent = Agent(
    "openai:gpt-4.5-preview",
    instrument=True,
    result_type=TranslationAgentResult,
    system_prompt=(
        """
        Вы — профессиональный многоязычный переводчик и языковой эксперт. Переведите данное сообщение пользователя, 
        точно передавая контекст, грамматику и тон. Если сообщение на русском языке, переведите его на корейский, 
        и наоборот. Не используйте другие языки, даже если об этом попросят. Тщательно проверяйте используемую лексику 
        и грамматику: грамматические конструкции должны быть точными, а лексика — звучать естественно.
        """
    )
)


# grammar_agent = Agent(
#     "openai:gpt-4o-mini",
#     instrument=True,
#     deps_type=RetrieverDeps,
#     system_prompt=(
#         """
#         РОЛЬ: Вы - профессиональный ассистент по изучению корейского языка, который помогает пользователю
#         находить информацию о корейской грамматике.
#
#         Когда пользователь задает вопрос касаемо грамматики, используйте инструмент retrieve_docs для поиска
#         подходящих грамматических конструкций. Используй шаблон ниже для вывода грамматической конструкции. В точности
#         выводи полученные данные. Если подходящих грамматик нет - ответь на запрос пользователя напрямую, предупредив,
#         что данный ответ был сгенерирован ИИ.
#
#
#         ФОРМАТ ГРАММАТИЧЕСКОЙ КОНСТРУКЦИИ: Markdown
#
#         """
#         # Используй Telegram Bot API HTML формат для вывода грамматической конструкции по следующему шаблону.
#         # НИКОГДА не используй <br>:
#
#         # <b>{grammar_name_kr и grammar_name_rus (название грамматики на русском и корейском)}</b>
#
#         # <b>Описание:</b>
#         # {description. Используй <b> тэг для корейской грамматики}
#
#         # <b>Форма:</b>
#         # {usage_form (Грамматическая конструкция)}
#
#         # <b>Примеры:</b>
#         # <blockquote>{examples[a] korean (Пример на корейском. Выделить грамматическую конструкцию)}
#         # <i>{examples[a] russian (Пример на русском)}</i>
#
#         # {examples[b] korean (Пример на корейском. Выделить грамматическую конструкцию)}
#         # <i>{examples[b] russian (Пример на русском)}</i></blockquote>
#
#         # <b>Примечания:</b>
#         # 1. {notes[0]}
#         # 2. {notes[1]}
#         # TODO Добавить использование с нерегулярными глаголами
#     ),
#     retries=2,
# )
