from dataclasses import dataclass
from typing import Literal, Optional, List, Dict

from fastembed import SparseTextEmbedding
from openai import AsyncOpenAI
from pydantic import BaseModel
from qdrant_client import QdrantClient
    

@dataclass
class RouterAgentDeps:
    openai_client: AsyncOpenAI
    sparse_embedding: SparseTextEmbedding
    # TODO: Add async support using AsyncQdrantClient
    qdrant_client: QdrantClient
    

class TranslationAgentResult(BaseModel):
    translation: str = ""


class RouterAgentResult(BaseModel):
    llm_response: str
    mode: Literal["answer", "vocab"] = "answer"


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


class RetrievedDocs(BaseModel):
    content: GrammarEntry
    score: float
    cross_score: Optional[float] = None

