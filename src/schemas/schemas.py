from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    content: str