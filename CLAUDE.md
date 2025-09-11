# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Korean Learning Bot - Dev Guidelines

## Commands
- **Run bot**: `uv run python3 -m src.tgbot.bot`
- **Run API**: `uv run fastapi dev src/api/main.py`
- **Run all services**: `docker compose up`
- **Linting**: `ruff check .`
- **DB migrations**: 
  - Apply: `alembic upgrade head`
  - Create: `alembic revision --autogenerate -m "message"`

## Architecture Overview

### Core Components
This is a **multi-agent Korean language learning chatbot** with the following architecture:

1. **Telegram Bot** (`src/tgbot/`): Front-end interface using aiogram 3.x
2. **FastAPI Backend** (`src/api/`): REST API that orchestrates LLM agents
3. **Multi-Agent LLM System** (`src/llm_agent/`): Specialized agents for different response types
4. **Vector Database** (`src/qdrant_db/`): Qdrant for semantic search of Korean grammar and lessons
5. **PostgreSQL Database** (`src/db/`): User management and message history storage

### Agent System
The bot uses **4 specialized agents**:
- **Router Agent**: Classifies user messages into types (direct grammar search, thinking grammar answer, casual answer)
- **HyDE Agent**: Rewrites queries for better vector search using Hypothetical Document Embeddings
- **Thinking Grammar Agent**: Provides detailed explanations with RAG-based document retrieval
- **System Agent**: Handles casual conversations and general bot interactions

### Message Flow
1. User sends message via Telegram → Bot forwards to API (`/invoke`)
2. Router agent classifies message type
3. Appropriate agent processes request (with optional vector search)
4. Response formatted and sent back through Telegram

### Database Schema
- **UserModel**: Stores Telegram users with BigInteger IDs
- **MessageBlobModel**: Stores conversation history as binary blobs with is_active flag

## Development Setup

### Dependencies
- **Python 3.12+** with UV package manager
- **PostgreSQL 15** (exposed on port 5433)
- **Qdrant** vector database (ports 6333/6334)
- **OpenAI API** for LLM agents
- **Telegram Bot Token** for bot functionality

### Environment Variables
Required in `.env` file:
- `BOT_TOKEN`: Telegram bot token
- `ADMIN_IDS`: List of admin user IDs
- `OPENAI_API_KEY`: OpenAI API key
- `POSTGRES_*`: Database connection details
- `LOGFIRE_API_KEY`: For observability
- `KRDICT_API_KEY`: Korean dictionary API

### Data Structure
- `/data/grammar-level-1/`: Korean grammar rules in markdown format
- `/data/howtostudykorean/`: Lesson content for RAG system
- `/src/qdrant_db/qdrant_data/`: Vector database storage

## Code Style
- Use **type hints** for all function parameters and return values
- Follow **async/await** patterns consistently
- **Imports**: group std lib, 3rd party, local imports with blank line between
- **Error handling**: use try/except with specific exceptions, log with logfire
- **Naming**:
  - snake_case for variables, functions
  - CamelCase for classes
  - UPPER_CASE for constants
- Organize Telegram bot handlers by feature in separate modules
- Use Pydantic for data validation and settings
- Follow CRUD pattern for database operations
- Document complex functions with docstrings

## Key Patterns

### Agent Tools
Tools are defined in `src/llm_agent/agent_tools.py` and use **dependency injection** pattern with context types like `RouterAgentDeps` and `ThinkingGrammarAgentDeps`.

### Message History
Uses **Pydantic AI message format** stored as binary blobs in PostgreSQL. Active messages are tracked with `is_active` boolean flag.

### Vector Search
Implements **hybrid search** with:
- Dense embeddings (text-embedding-3-small)
- Sparse embeddings (Qdrant/bm25)
- Late interaction model (jinaai/jina-colbert-v2)

### Error Handling
User authentication required - only registered users can access the bot. Requests from unregistered users return 403 Forbidden.