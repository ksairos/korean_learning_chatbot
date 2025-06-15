from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from fastembed import SparseTextEmbedding
from openai import AsyncOpenAI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder
from sqlalchemy.ext.asyncio import AsyncSession


class GrammarEntry(BaseModel):
    level: Literal[1, 2, 3, 4, 5, 6]
    grammar_name_kr: str
    grammar_name_rus: str
    description: str
    usage_form: str
    examples: List[Dict[str, str]]
    notes: Optional[List[str]]
    # TODO: Add irregular verbs examples
    # with_irregular_verbs: Optional[List[str]]
    

class GrammarEntryV2(BaseModel):
    grammar_name: str
    level: Literal[1, 2, 3, 4, 5, 6]
    content: str

class RetrievedDoc(BaseModel):
    content: GrammarEntryV2
    score: float
    cross_score: Optional[float] = None


class TelegramUser(BaseModel):
    """
    Schema for Telegram user data for TelegramMessage
    """

    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    chat_id: int


class TelegramMessage(BaseModel):
    """
    Schema for telegram message sent from Telegram to API
    """

    user_prompt: str
    user: TelegramUser

@dataclass
class RouterAgentDeps:
    openai_client: AsyncOpenAI
    # TODO: Add async support using AsyncQdrantClient
    qdrant_client: QdrantClient
    sparse_embedding: SparseTextEmbedding
    reranking_model: CrossEncoder
    session: AsyncSession


class TranslationAgentResult(BaseModel):
    translation: str = ""


class RouterAgentResult(BaseModel):
    user_message: str
    message_type: Literal[
        "direct_grammar_search",
        "thinking_grammar_answer",
    ] = "direct_grammar_answer"

class GrammarAgentResult(BaseModel):
    llm_response: str
    answer_type: str = "grammar"

class GrammarSearchAgentResult(BaseModel):
    found_grammars: list[str | None]
