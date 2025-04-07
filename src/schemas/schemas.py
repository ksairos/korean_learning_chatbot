from dataclasses import dataclass
from typing import Literal, Optional, List, Dict

from fastembed import SparseTextEmbedding
from openai import AsyncOpenAI
from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient, QdrantClient


@dataclass
class RetrieverDeps:
    openai_client: AsyncOpenAI
    sparse_embedding: SparseTextEmbedding
    qdrant_client: QdrantClient


class ChatMessage(BaseModel):
    content: str


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
    
    