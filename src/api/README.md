# API Package

## Purpose
FastAPI-based REST API service that serves as the backend for the Korean learning chatbot. It receives messages from the Telegram bot and orchestrates the LLM agent responses.

## Key Components
- **main.py**: FastAPI application with `/invoke` endpoint for processing user messages
- Routes user messages through multiple specialized agents based on message type
- Handles user authentication and message history management
- Integrates with OpenAI, Qdrant vector database, and PostgreSQL database

## Dependencies
- **src/llm_agent/**: Uses router, grammar search, thinking grammar, and system agents
- **src/db/**: Database operations for user management and message history
- **src/schemas/**: Pydantic models for request/response validation
- **src/config/**: Configuration and settings management

## Usage
Start the API server:
```bash
uv run fastapi dev src/api/main.py
```

The API exposes:
- `GET /`: Health check endpoint
- `POST /invoke`: Main endpoint for processing Telegram messages

## Message Flow
1. Receives `TelegramMessage` from Telegram bot
2. Authenticates user against registered users
3. Routes to appropriate agent based on message type classification
4. Returns formatted response with processing mode indicator