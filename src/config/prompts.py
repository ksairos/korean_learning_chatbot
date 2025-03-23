from pydantic_settings import BaseSettings


class Prompts(BaseSettings):
    
    answer_generation: str = (
        """
        You are a helpful assistant that uses the following context to answer the user's query. 
        Use the user query to provide an accurate and informative response.
        """
    )


prompts = Prompts()