from pydantic_ai import Agent
from schemas.schemas import ResponseModel
from rich import print_json, print

agent = Agent(
    'openai:gpt-4o-mini',
    result_type=ResponseModel,
    system_prompt="You are a helpful assistant. Answer in 1 sentence",
)

async def main():
    response = await agent.run("My name is Alex. I want to know what is the capital of France?")
    print(response.data)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())