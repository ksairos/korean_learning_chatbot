from typing import Literal, List

import logfire

from dotenv import load_dotenv
from pydantic_ai.usage import UsageLimits

from src.config.prompts import prompts
from src.config.settings import Config

from pydantic_ai import Agent, RunContext


from src.llm_agent.agent_tools import retrieve_docs_tool
from src.utils.json_to_telegram_md import grammar_entry_to_markdown
from src.schemas.schemas import (
    RouterAgentDeps,
    RouterAgentResult,
    RetrievedDoc,
    GrammarSearchAgentResult,
    GrammarAgentResult,
    GrammarEntryV2,
)

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
    model="openai:gpt-4o",
    instrument=True,
    output_type=RouterAgentResult,
    instructions="""
        Analyze and classify the user prompt
        1. The user is looking for a description of a specific Korean grammar, either in Russian or Korean. Set message_type=direct_grammar_search
        2. The user needs an explanation of a grammar structure or a grammar related question (meaning, grammar description output alone is not enough). Set message_type=thinking_grammar_answer
    """
)

grammar_agent = Agent(
    model="openai:gpt-4o",
    instrument=True,
    output_type=GrammarAgentResult,
    instructions="""
        Ты - профессиональный ИИ ассистент LazyHangeul. Твоя задача - помогать пользователям в изучении корейской грамматики. Следуй следующим правилам, в зависимости от message_type:
        ## direct_grammar_search
        Используй `call_grammar_search_agent`, чтобы вывести найденные грамматики
        - Если call_grammar_search_agent вывел только одну грамматику - выведи её пользователю в изначальном виде
        - Если call_grammar_search_agent вывел несколько грамматик, предоставь пользователю список этих грамматик и предложи выбрать одну
        
        ## thinking_grammar_answer
        Отвечай напрямую, не используя инструменты
    """
)

# @grammar_agent.tool
# async def call_grammar_search_agent(context: RunContext[RouterAgentDeps], user_prompt: str):
#     r = await grammar_search_agent.run(
#         user_prompt,
#         deps=context.deps,
#         usage_limits=UsageLimits(request_limit=5),
#         output_type=List[GrammarEntryV2 | None]
#     )
#     return r.output.found_grammars

grammar_search_agent = Agent(
    model="openai:gpt-4o",
    instrument=True,
    instructions="""
        Ты - мощный поисковик корейских грамматик. Обработай запрос пользователя и найти соответствующие грамматики:
        1. Обработка запроса перед использованием инструмента
        - Если пользователь ввел слово, содержащее грамматическую конструкцию, извлеките грамматическую форму 
        или шаблон в её изначальном виде для дальнейшего поиска. К примеру, если запрос пользователя содержит
        "가고 싶어요", извлеките "고 싶다".
        - Если пользователь запрашивает грамматику на русском языке, используйте только её ("грамматика будущего 
        времени в корейском" -> "будущее время")
        
        2. Используйте извлеченную грамматику для поиска соответствующего объяснения с помощью инструмента `grammar_search`
        
        3. Найденные грамматики должны быть выведены строго в том формате, в котором они были получены!
        
        ---
        
        Если ничего не найдено - выведите пустой список
    """,
    output_type=List[GrammarEntryV2] 
)


@grammar_search_agent.tool
async def grammar_search(context: RunContext[RouterAgentDeps], search_query: str) -> List[GrammarEntryV2] | None:
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.
    Args:
        context: the call context
        search_query: запрос для поиска
    """
    docs = await retrieve_docs_tool(context, search_query)
    if docs:
        llm_filter_prompt = [f"ЗАПРОС ПОЛЬЗОВАТЕЛЯ: '{search_query}'\n\СПИСОК КОРЕЙСКИХ ГРАММАТИК: "]
        for i, doc in enumerate(docs):
            #! For Version 1 grammars (full in json)
            llm_filter_prompt.append(f"{i}. {doc.grammar_name_kr} - {doc.grammar_name_rus}")

            #! For Version 2 grammars (MD)
            # llm_filter_prompt.append(f"{i}. {doc}")
        
        llm_filter_agent = Agent(
            model="openai:gpt-4o",
            instrument=True,
            output_type=List[int],
            instructions="""
                На основе ЗАПРОСА ПОЛЬЗОВАТЕЛЯ выберите соответствующие результаты поиска из СПИСКА ГРАММАТИКИ и выведите только их индексы.
            """
        )
        
        llm_filter_response = await llm_filter_agent.run(user_prompt="\n\n".join(llm_filter_prompt))
        filtered_doc_ids = llm_filter_response.output
        filtered_docs =[docs[i] for i in filtered_doc_ids]

        logfire.info(f"LLM filtered docs: {filtered_docs}")
        return filtered_docs
    return None


# @router_agent.tool
# async def output_single_doc(context: RunContext[RouterAgentDeps], search_query: str):
#     """
#     Инструмент для поиска грамматической конструкций на основе запроса пользователя.
#     A tool for extracting grammatical constructions based on the user's query.
#     Args:
#         context: the call context
#         search_query: запрос для поиска
#     """
#     pass
#

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



# @router_agent.tool_plain
# async def translation_agent_call(user_prompt: str):
#     """
#     Инструмент для перевода текста с русского на корейский и наоборот.
#     A tool for translating text from Russian to Korean and vice versa.
#     Args:
#         user_prompt: запрос для перевода
#     """
#     r = await translation_agent.run(user_prompt, output_type=TranslationAgentResult)
#     return r.output.translation
#
#
# translation_agent = Agent(
#     "openai:gpt-4.5-preview",
#     instrument=True,
#     output_type=TranslationAgentResult,
#     instructions=translator_prompt
# )
