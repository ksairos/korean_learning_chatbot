from typing import List

import logfire

from dotenv import load_dotenv

from src.config.prompts import prompts
from src.config.settings import Config

from pydantic_ai import Agent, RunContext


from src.llm_agent.agent_tools import retrieve_docs_tool
from src.schemas.schemas import (
    RouterAgentDeps,
    RouterAgentResult,
    GrammarEntryV2,
)

load_dotenv()

config = Config()
logfire.configure(token=config.logfire_api_key)

#IMPORTANT Modify to change the bot language
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


grammar_search_agent = Agent(
    model="openai:gpt-4o",
    instrument=True,
    instructions="""
        1. Обработка запроса перед использованием инструмента
        - Если пользователь ввел слово, содержащее грамматическую конструкцию, извлеките грамматическую форму 
        или шаблон в её изначальном виде для дальнейшего поиска. К примеру, если запрос пользователя содержит
        "가고 싶어요", извлеките "고 싶다".
        - Если пользователь запрашивает грамматику на русском языке, используйте только её ("грамматика будущего 
        времени в корейском" -> "будущее время")
        
        2. Используйте извлеченную грамматику для поиска соответствующего объяснения с помощью инструмента `grammar_search`
        
        ВАЖНО: найденные грамматики должны быть выведены строго в том формате, в котором они были получены!
        
        Если ничего не найдено - выведите пустой список
    """,
    output_type=list[GrammarEntryV2 | None]
)


thinking_grammar_agent = Agent(
    model="openai:gpt-4o",
    instrument=True,
    output_type=str,
    instructions="""
        РОЛЬ: Ты - профессиональный ИИ ассистент LazyHangeul, натренерованный на преподавание корейской грамматики. 
        ТВОЯ ЗАДАЧА: Помогать пользователям в изучении корейской грамматики.
    """
)


@grammar_search_agent.tool
async def grammar_search(context: RunContext[RouterAgentDeps], search_query: str) -> list[GrammarEntryV2 | None]:
    """
    Инструмент для извлечения грамматических конструкций на основе запроса пользователя.
    A tool for extracting grammatical constructions based on the user's query.
    Args:
        context: the call context
        search_query: запрос для поиска
    """
    docs: list[GrammarEntryV2] | None = await retrieve_docs_tool(context, search_query)
    if docs:
        llm_filter_prompt = [f"USER_QUERY: '{search_query}'\n\nGRAMMAR LIST: "]
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
                Based on the USER QUERY select appropriate search results from the GRAMMAR LIST, and output their index only
            """
        )
        llm_filter_response = await llm_filter_agent.run(user_prompt="\n\n".join(llm_filter_prompt))
        filtered_doc_ids = llm_filter_response.output
        filtered_docs = [docs[i] for i in filtered_doc_ids]

        logfire.info(f"LLM filtered docs: {filtered_docs}")
        return filtered_docs
    return []
