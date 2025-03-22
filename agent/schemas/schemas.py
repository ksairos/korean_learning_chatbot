from pydantic import BaseModel
from typing import Literal

class ResponseModel(BaseModel):
    """Response model for LLM"""
    response: str
    username: str | None
    topic: Literal[""]