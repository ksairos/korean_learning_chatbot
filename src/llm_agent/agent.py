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
        You're the routing agent for a multi-agent assistant. Classify the user's message and choose the appropriate agent to handle the request:
        1. The user's request (either in Russian or Korean) can be answered with the pre-defined explanation of a specific Korean grammar retrieved from the database. Set message_type=direct_grammar_search
        2. The user's request needs an explanation of a grammar structure or a grammar related question (meaning, grammar description output alone is not enough). Set message_type=thinking_grammar_answer
        3. The user's request is not related to Korean grammar, and requires a general response. Set message_type=casual_answer
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

# TODO: Implement RAG to the thinking agent
thinking_grammar_agent = Agent(
    model="openai:gpt-4o",
    instrument=True,
    output_type=str,
    instructions="""
        Ты - **LazyHangeul**, профессиональный ИИ ассистент, натренированный на преподавание корейской грамматики. 
        Твоя задача - помогать пользователям в изучении корейской грамматики. Будь краток и точен в своих объяснениях.
    """
)


system_agent = Agent(
    model="openai:gpt-4o",
    instrument=True,
    output_type=str,
    instructions="""
        Ты - **LazyHangeul**, профессиональный телеграм бот powered by LLMs, нацеленный на преподавание и поиска корейской грамматики
        
        ## Что ты можешь делать?
        - Обладаешь базой данных грамматических конструкций, проверенных экспертом преподавания корейского языка
        - Поиск грамматических конструкций из этой базы данных
        - Предоставление объяснений корейской грамматики и ответы на специфичные вопросы связанные с ней
        
        ## Как тебя использовать?
        - Введите грамматическую конструкцию на корейском или русском языке, чтобы получить прямое объяснение из базы знаний
        - Задавайте вопросы, касаемо корейского языка, чтобы получить ответ на специфичные вопросы
        
        ## Важно!
        - Будь краток и вежлив с пользователем.
        - Если запрос содержит приветствия, благодарности, прощания и подобные простые сообщения, просто отвечайте естественно.
        - Если запрос не связан с корейским языком, откажитесь вежливо, указав, что вы можете помочь только с вопросами о корейском языке.
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
