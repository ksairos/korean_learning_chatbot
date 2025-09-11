# API Package

## Purpose
FastAPI-based REST API service that serves as the orchestration layer for the Korean learning chatbot. It receives messages from the Telegram bot and coordinates responses through a sophisticated multi-agent LLM system.

## Architecture
This API implements a **multi-agent orchestration pattern** where incoming user messages are:
1. **Classified** by a router agent into message types
2. **Processed** by specialized agents based on the classification
3. **Enhanced** with vector search for grammar and lesson content
4. **Tracked** with comprehensive message history and observability

## Key Components

### Core Files
- **main.py**: Main FastAPI application with comprehensive agent orchestration
- **routers/evaluation.py**: Evaluation endpoints for testing and monitoring

### Agent Integration Points
The API coordinates between 4 specialized agents:
- **Router Agent**: Classifies messages into `direct_grammar_search`, `thinking_grammar_answer`, or `casual_answer`
- **HyDE Agent**: Rewrites queries using Hypothetical Document Embeddings for better vector search
- **Thinking Grammar Agent**: Provides detailed explanations with RAG-based context retrieval
- **System Agent**: Handles casual conversations and general bot interactions

### Response Modes
- **single_grammar**: Returns one grammar entry directly from vector search
- **multiple_grammars**: Returns grammar selection menu when multiple matches found
- **thinking_grammar_answer**: Returns detailed explanation with optional RAG context
- **casual_answer**: Returns general conversational response
- **no_grammar**: Fallback when no grammar found but thinking response needed

## Dependencies
- **src/llm_agent/**: Multi-agent system with specialized tools
- **src/db/**: PostgreSQL operations for users and message history
- **src/schemas/**: Pydantic models for request/response validation
- **src/config/**: Environment configuration and settings
- **OpenAI**: GPT-4 models for agent inference
- **Qdrant**: Vector database for semantic search
- **Logfire**: Observability and tracing

## Usage

### Development Server
```bash
# Start API in development mode
uv run fastapi dev src/api/main.py

# Or via Docker Compose
docker compose up api
```

### Production
```bash
# Start with uvicorn directly
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```http
GET /
```
Returns simple health check message.

### Message Processing
```http
POST /invoke
Content-Type: application/json

{
  "user_prompt": "string",
  "user": {
    "user_id": 123456789,
    "username": "string",
    "first_name": "string",
    "last_name": "string"
  }
}
```

**Response Format:**
```json
{
  "llm_response": "string or array",
  "mode": "single_grammar|multiple_grammars|thinking_grammar_answer|casual_answer|no_grammar"
}
```

### Evaluation Routes
See `routers/evaluation.py` for testing and evaluation endpoints.

## Authentication
- **User Registration Required**: Only users in the database can access the API
- **403 Forbidden**: Returned for unregistered users
- **Admin Management**: Admins can manage user registration via Telegram bot

## Message History
- **Automatic Tracking**: All conversations stored in PostgreSQL as binary message blobs
- **Pydantic AI Format**: Uses Pydantic AI message format for consistency
- **Context Window**: Last 2 messages used for agent context
- **Background Processing**: Message history updated asynchronously

## Vector Search Integration
- **Hybrid Search**: Combines dense + sparse + late interaction embeddings
- **Multiple Collections**: Separate collections for grammar rules and lesson content
- **HyDE Enhancement**: Query rewriting for better semantic matching
- **Fallback Handling**: Graceful degradation when vector search fails

## Observability
- **Logfire Integration**: Comprehensive tracing with structured logs
- **User Tagging**: All logs tagged with user IDs for debugging
- **Performance Monitoring**: Request timing and agent response tracking
- **Error Handling**: Detailed error logging with context preservation