from typing import List, Union

import logfire

from dotenv import load_dotenv

from src.config.settings import Config

from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings


from src.schemas.schemas import (
    RouterAgentDeps,
    RouterAgentResult,
    GrammarEntryV2,
)

load_dotenv()

config = Config()

router_agent = Agent(
    model="openai:gpt-4.1",
    instrument=True,
    output_type=RouterAgentResult,
    model_settings=ModelSettings(temperature=0.0),
    instructions="""
        You're the routing agent for a multi-agent assistant. Classify the user's message and choose the appropriate agent to handle the request:
        1. The user's request can be answered with the comprehensive explanation of a specific Korean grammar. Set message_type=direct_grammar_search
        2. The user's request needs a more detailed explanation of a grammar structure or a grammar related question (meaning, grammar description output alone is not enough). Set message_type=thinking_grammar_answer
        3. The user's request is not related to Korean grammar, and requires a general response. Set message_type=casual_answer
        Follow-up questions should be tagged as message_type=thinking_grammar_answer
    """
)


query_rewriter_agent = Agent(
    model="openai:gpt-4.1-mini",
    instrument=True,
    instructions="""
        Вы - мощный query rewriter в мульти-агентной системе по изучению корейской грамматики.
        - Если пользователь ввел слово, содержащее грамматическую конструкцию, извлеките грамматическую форму 
        или шаблон в её изначальном виде для дальнейшего поиска. К примеру, если запрос пользователя содержит
        "가고 싶어요", извлеките "고 싶다".
        - Если пользователь запрашивает грамматику на русском языке, используйте только её ("грамматика будущего 
        времени в корейском" -> "будущее время")
        
        Если ничего не найдено - выведите None
    """,
    output_type= Union[str|None]
)

hyde_agent = Agent(
    model="openai:gpt-4.1",
    instrument=True,
    instructions="""
            Ты - профессиональный преподаватель корейского языка. Учитывая вопрос пользователя, сгенерируйте гипотетический ответ, 
            который напрямую отвечает на этот вопрос. Текст должен быть кратким и содержать только необходимую информацию. 
            Уместите ответ в 2-3 предложениях
        """
)

thinking_grammar_agent = Agent(
    model="openai:gpt-4.1-mini",
    instrument=True,
    instructions="""
        Ты - профессиональный агент в RAG системе в роли преподавателя корейского языка. Основываясь на предоставленной информации RETRIEVED DOCS, 
        сформируйте краткий, четкий и точный ответ на запрос пользователя. При необходимости используйте примеры из этой же информации. 
        Если документов нет или они не подходят для ответа на запрос, постарайтесь ответить на запрос пользователя самостоятельно.
    """
)

@thinking_grammar_agent.instructions
def add_docs(ctx: RunContext[list]) -> str:
    docs = ["RETRIEVED DOCS:"]
    for i, doc in enumerate(ctx.deps):
        docs.append(f"{i}. {doc.content["content"]}")
    return "\n\n".join(docs)


system_agent = Agent(
    model="openai:gpt-4.1-mini",
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


summarize_agent = Agent(
    'openai:gpt-4.1-mini',
    instructions="""
    Summarize this conversation, omitting small talk and unrelated topics.
    Focus on the essentials of the discussion and next steps
    """,
)