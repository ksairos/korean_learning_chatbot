import logfire

from dotenv import load_dotenv

from src.config import prompts

from pydantic_ai import Agent

load_dotenv()
logfire.configure(send_to_logfire="if-token-present")

agent = Agent(
    "openai:gpt-4o-mini",
    instrument=True,
    system_prompt=prompts.prompts.answer_generation,
    retries=2
)