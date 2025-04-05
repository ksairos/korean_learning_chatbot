from dataclasses import dataclass
from typing import Literal, Optional

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

class RetrievedDocs(BaseModel):
    content: str
    metadata: dict
    score: float
    cross_score: Optional[float] = None


