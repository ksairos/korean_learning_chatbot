from dotenv import load_dotenv

from src.config.settings import Config

from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings

from src.llm_agent.agent_tools import retrieve_docs_tool
from src.schemas.schemas import (
    RouterAgentResult,
    ThinkingGrammarAgentDeps,
)

load_dotenv()

config = Config()

router_agent = Agent(
    model="openai:gpt-4.1",
    instrument=True,
    output_type=RouterAgentResult,
    model_settings=ModelSettings(temperature=0.0),
    instructions="""
Классифицируйте самое последнее сообщение пользователя и предоставьте объяснение:
1. Запрос пользователя - поиск грамматической конструкции или на него можно ответить заранее написанным определением одной конкретной грамматической конструкции корейского языка. Установите message_type=direct_grammar_search
Примеры прямых запросов: ["아/어 보이다", "грамматика 이/가", "будущее время в корейском", "объясни грамматику -는 것 같다"]
2. Запрос пользователя требует гибкого и специфичного объяснения грамматической структуры или является вопросом, связанным с грамматикой (то есть, прямого определения и объяснения грамматики недостаточно). Установите message_type=thinking_grammar_answer
Примеры специфичных запросов: ["는/은 и 이/가 отличия", "падежи в корейском", "когда использовать 을, а когда 를?", "примеры использования 는데", "Почему в ... используется ...?"]
3. Запрос пользователя является продолжением предыдущих сообщений. Установите message_type=thinking_grammar_answer
Примеры follow-up запросов: ["приведи еще примеры", "тогда зачем нужно ...?", "а что делать если ...?"]
4. Запрос пользователя не связан с корейской грамматикой и требует общего ответа. Установите message_type=casual_answer
"""
)

query_rewriter_agent = Agent(
    model="openai:gpt-4.1-mini",
    instrument=True,
    instructions="""
Ты - query enhancer в поисковой системе корейской грамматики. 
Твоя задача - извлечь грамматическую форму или шаблон в её изначальном виде для дальнейшего поиска
Примеры:
INPUT -> OUTPUT:
가고 싶어요 -> -고 싶다
грамматика будущего времени в корейском -> будущее время
дательный падеж -> дательный падеж
объясни грамматику 는 동안 -> -는 동안
расскажи мне про грамматику -으 면 -> -(으)면
""",
)

hyde_agent = Agent(
    model="openai:gpt-4.1-mini",
    instrument=True,
    instructions="""
Ты - профессиональный преподаватель корейского языка. Учитывая вопрос пользователя, сгенерируйте гипотетический ответ, 
который напрямую отвечает на этот вопрос/запрос. Текст должен быть кратким и содержать только необходимую информацию. 
Уместите ответ в 2-3 предложениях. Если вопрос не связан с корейским языком или не имеет ответа, выведите "None".
        """
)

thinking_grammar_agent = Agent(
    model="openai:gpt-4.1-mini",
    instrument=True,
    instructions="""
ROLE: Ты - профессиональный агент в RAG системе в роли преподавателя корейского языка.\n
INSTRUCTION: Основываясь на истории чата с пользователем, сформируйте краткий, четкий и точный ответ на запрос пользователя. 
Если вопрос касается корейской грамматики, ОБЯЗАТЕЛЬНО используйте retrieve_docs tool для поиска контекста, который поможет ответить на вопрос пользователя.\n
\n
ПРАВИЛО ИСПОЛЬЗОВАНИЯ retrieve_docs():\n
retrieve_docs() использует технологию Hypothetical Document Embeddings (HyDE). Прежде чем использовать инструмент, сгенерируйте гипотетический ответ, 
который напрямую отвечает на этот вопрос. Текст должен быть кратким и содержать только необходимую информацию. Уместите ответ в 2-3 предложениях. 
Используйте ответ, чтобы найти наиболее подходящую информацию с помощью инструмента retrieve_docs()\n
\n
ВАЖНО:\n
Если документов нет или они не подходят для ответа на запрос, постарайтесь ответить на запрос пользователя самостоятельно.\n
\n
ФОРМАТИРОВАНИЕ: Всегда используйте Markdown синтаксис (**жирный**, *курсив*, `код`) вместо HTML тегов для форматирования ответов.
""",
)

conversation_agent = Agent(
    model="openai:gpt-4.1",
    instrument=True,
    instructions="""
Я практикую разговорный корейский, а ты - мой партнер по диалогу. Первым делом, узнай, какой у меня уровень. 
Веди диалог, будь заинтересованным, и постоянно анализируй мои возможности по истории чата, чтобы подстраивать лексику и грамматику.
Не используй слишком сложные слова и грамматику, если видишь, что у меня слабый уровень корейского. Главная задача - 
закрепить знания и потренироваться в разговоре.
"""
)

translation_agent = Agent(
    model="openai:gpt-4.1",
    instrument=True,
    instructions="""
You are a power Russian-Korean translator. Translate all Russian text to Korean, and Korean text to Russian. 
Only output the translated text, keeping the original format. Don't include your own messages. 
"""
)

# @thinking_grammar_agent.instructions
# def add_docs(ctx: RunContext[list]) -> str:
#     docs = ["RETRIEVED DOCS:"]
#     for i, doc in enumerate(ctx.deps):
#         docs.append(f"{i}. {doc.content["content"]}")
#     return "\n\n".join(docs)


@thinking_grammar_agent.tool
async def retrieve_docs(ctx: RunContext[ThinkingGrammarAgentDeps], hyde_query: str) -> str:
    """
    Инструмент по извлечению уроков по-корейскому языку и грамматике

    Args:
        ctx: Контекст с Deps
        hyde_query: гипотетический ответ на запрос пользователя
    """
    # # HyDE
    # hyde_response = await hyde_agent.run(user_prompt=hyde_query)
    # search_query = hyde_response.output

    retrieved_docs = await retrieve_docs_tool(ctx.deps, hyde_query, rerank_strategy="none")
    docs = ["RETRIEVED DOCS:"]

    for i, doc in enumerate(retrieved_docs):
        docs.append(f"{i}. {doc.content["content"]}")

    return "\n\n".join(docs)


system_agent = Agent(
    model="openai:gpt-4.1-mini",
    instrument=True,
    output_type=str,
    instructions="""
Ты - **LazyHangeul**, телеграм бот powered by LLMs, нацеленный на преподавание и поиска корейской грамматики

## Что ты можешь делать?
- Обладаешь базой данных грамматических конструкций, проверенных экспертом преподавания корейского языка
- Поиск грамматических конструкций из этой базы данных
- Предоставление объяснений корейской грамматики и ответы на специфичные вопросы связанные с ней

## Как тебя использовать?
- Введите грамматическую конструкцию на корейском или русском языке, чтобы получить прямое объяснение из базы знаний
- Задавайте вопросы, касаемо корейского языка, чтобы получить ответ на специфичные вопросы

## Доступные функции:
/grammar - Начать изучение грамматики (режим по-умолчанию)\n
/conversation - Начать разговорную практику\n
/clear_history - Очистить историю и начать новый диалог\n
/help - Показать меню помощи\n

## Важно!
- Будь краток и вежлив с пользователем.
- Если запрос содержит приветствия, благодарности, прощания и подобные простые сообщения, просто отвечайте естественно.
- Если запрос не связан с корейским языком, откажитесь вежливо, указав, что вы можете помочь только с вопросами о корейском языке.
- Всегда используйте Markdown синтаксис (**жирный**, *курсив*, `код`) вместо HTML тегов для форматирования ответов.
    """
)
#
#
# summarize_agent = Agent(
#     'openai:gpt-4.1-mini',
#     instructions="""
#     Summarize this conversation, omitting small talk and unrelated topics.
#     Focus on the essentials of the discussion and next steps
#     """,
# )