# LLM Agent Package

## Purpose
Implements a multi-agent system for processing Korean language learning queries using OpenAI's GPT models. Routes user messages to specialized agents based on query type and integrates with RAG (Retrieval-Augmented Generation) for grammar search.

## Key Components
- **agent.py**: Defines four specialized agents with distinct roles
- **agent_tools.py**: RAG tools for grammar retrieval from Qdrant vector database
- **agent_tools_old.py**: Legacy tool implementations

## Agents
- **router_agent**: Classifies user messages into categories (grammar search, thinking answer, casual)
- **grammar_search_agent**: Searches grammar database and filters results using LLM
- **thinking_grammar_agent**: Provides explanations for grammar-related questions
- **system_agent**: Handles general chatbot interactions and non-grammar queries

## Dependencies
- **src/qdrant_db/**: Vector database integration for grammar retrieval
- **src/schemas/**: Pydantic models for agent input/output
- **src/config/**: Prompts and configuration settings

## Key Features
- Message routing based on content classification
- RAG-powered grammar search with semantic similarity
- Multi-language support (Russian/English interfaces)
- LLM-based result filtering and relevance scoring
- Instrumentation with Logfire for monitoring

## Usage
Agents are invoked through the API layer with:
```python
router_agent.run(user_prompt=message, deps=deps, output_type=RouterAgentResult)
```

## Language Configuration
Bot language is configured via the `language` variable in agent.py (currently set to "ru" for Russian).