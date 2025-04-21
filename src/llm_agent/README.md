# LLM Agent Module

This module provides the core natural language processing capabilities for the Korean Learning Bot, implementing different LLM-powered agents that handle various user interactions.

## Core Features

- Router agent for intent classification and message routing
- Translation agent for Korean-Russian translation 
- Grammar agent for explaining Korean grammar concepts (planned)
- Document retrieval from vector database
- Hybrid search combining dense and sparse embeddings
- Cross-encoder reranking for improved result relevance

## Implementation Details

The module consists of the following key components:

1. **agent.py**: Implements the main agent functionality
   - RouterAgent for classifying user intent and routing to specialized agents
   - TranslationAgent for handling language translation requests
   - (Planned) GrammarAgent for explaining Korean grammar points

2. **agent_tools.py**: Provides specialized tools for the agents
   - retrieve_documents: Searches for relevant grammar documents
   - rerank_results: Uses cross-encoder to improve retrieval relevance
   - search_grammar: Semantic search for grammar points
   - rewrite_query: Planned tool to improve search queries

3. **utils/**: Supporting utilities
   - json_to_telegram_md.py: Converts structured JSON responses to Telegram-compatible markdown

The LLM agent module forms the AI brain of the Korean Learning Bot, providing intelligent responses and language learning assistance through specialized agents.