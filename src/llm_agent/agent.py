from typing import Dict, Any, Optional
import logfire

from dotenv import load_dotenv

from src.config import prompts
from src.schemas.schemas import (
    ChatMessage
)

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

load_dotenv()
logfire.configure(send_to_logfire="if-token-present")

class LLMAgent:
    def __init__(self, model_name: KnownModelName = "openai:gpt-4o-mini"):
        self.agent = Agent(
            model_name, 
            instrument=True,
            system_prompt=prompts.prompts.answer_generation,
            )

    async def query(self, user_prompt: str) -> str:
        response = await self.agent.run(user_prompt)
        logfire.info("Reponse: {response}", response=response)
        return response.data


agent = LLMAgent()