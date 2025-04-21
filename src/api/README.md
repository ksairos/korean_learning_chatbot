# API Module

The API module provides a FastAPI application that serves as the communication layer between the Telegram bot and the LLM agents. It exposes endpoints that process user messages and return appropriate responses.

## Core Features

- FastAPI server with `/invoke` endpoint for processing user requests
- Integration with OpenAI for text embeddings and LLM-powered responses
- Connects to Qdrant for vector search of Korean grammar concepts
- Uses cross-encoder for result re-ranking to improve relevance
- Manages message history through database sessions
- Implements hybrid search combining dense and sparse embeddings

## Implementation Details

The main FastAPI application handles:
- Processing incoming messages from the Telegram bot
- Routing requests to appropriate LLM agents based on message content
- Returning formatted responses ready for Telegram display
- Managing conversation context and message history

The API acts as the central hub for the application's AI capabilities, connecting the user interface (Telegram bot) with the backend LLM processing and vector database.