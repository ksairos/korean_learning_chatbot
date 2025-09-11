# LLM Agent Package

## Purpose
Implements a sophisticated multi-agent system for Korean language learning using OpenAI's GPT models and Pydantic AI framework. Features intelligent message routing, RAG-enhanced responses, and specialized agents for different query types.

## Architecture

### Multi-Agent Design Pattern
This package implements a **router-worker pattern** where:
1. **Router Agent** classifies incoming messages into categories
2. **Specialized Agents** handle specific types of queries with domain expertise
3. **Tool Integration** provides RAG capabilities and external data access
4. **Dependency Injection** ensures clean separation and testability

### Agent Orchestration Flow
```
User Message → Router Agent → Message Classification → Specialized Agent → Tools (if needed) → Response
```

## Core Components

### Agents (agent.py)

#### Router Agent
- **Model**: GPT-4.1 (high accuracy for classification)
- **Purpose**: Classifies user messages into categories
- **Output Types**:
  - `direct_grammar_search`: Direct grammar lookup requests
  - `thinking_grammar_answer`: Complex explanations needed
  - `casual_answer`: General conversational responses
- **Temperature**: 0.0 for consistent classification

#### HyDE Agent
- **Model**: GPT-4.1
- **Purpose**: Query rewriting using Hypothetical Document Embeddings
- **Function**: Generates hypothetical answers to improve vector search
- **Integration**: Used by thinking grammar agent for better retrieval

#### Thinking Grammar Agent  
- **Model**: GPT-4.1-mini (cost-effective for longer responses)
- **Purpose**: Provides detailed Korean grammar explanations
- **Features**:
  - RAG-based document retrieval via `retrieve_docs` tool
  - Fallback to internal knowledge when retrieval insufficient
  - Context-aware responses using conversation history

#### System Agent
- **Model**: GPT-4.1-mini
- **Purpose**: Handles casual conversations and bot interactions
- **Personality**: LazyHangeul - friendly Korean learning assistant
- **Capabilities**:
  - Greetings and casual conversation
  - Help and guidance
  - Polite refusal of non-Korean language topics

### Tools (agent_tools.py)

#### Grammar Retrieval Tool
```python
async def retrieve_grammars_tool(deps, search_query, retrieve_top_k=15)
```
- **Hybrid Search**: Combines dense + sparse + late interaction embeddings
- **Fusion Query**: Qdrant's fusion search for optimal results  
- **Score Thresholding**: Configurable quality filtering
- **Return Type**: `List[GrammarEntryV2]` with structured grammar data

#### Document Retrieval Tool
```python
async def retrieve_docs_tool(deps, hyde_query)
```
- **HyDE Enhancement**: Uses hypothetical document embeddings
- **Context Integration**: Incorporates conversation history
- **Fallback Handling**: Graceful degradation when no docs found
- **Return Type**: `List[RetrievedDoc]` with lesson content

### Dependency Injection System

#### RouterAgentDeps
- OpenAI client for embeddings
- Qdrant client for vector search
- Sparse embedding model
- Database session
- Late interaction model

#### ThinkingGrammarAgentDeps
- All RouterAgentDeps components
- Additional context for RAG operations

## Vector Search Implementation

### Hybrid Search Strategy
1. **Dense Embeddings**: text-embedding-3-small for semantic similarity
2. **Sparse Embeddings**: Qdrant/bm25 for keyword matching
3. **Late Interaction**: jinaai/jina-colbert-v2 for fine-grained relevance
4. **Fusion Query**: Combines all three approaches with RRF (Reciprocal Rank Fusion)

### Search Collections
- **Grammar Collections**: 
  - `korean_grammar_v2_small`: Main grammar rule database
  - `korean_grammar_v2`: Extended grammar database
- **Lesson Collections**:
  - `howtostudykorean_extended_small`: Lesson content for RAG
  - `howtostudykorean_extended`: Full lesson database

### Quality Filtering
- **Score Thresholds**: Configurable minimum similarity scores
- **Top-K Limiting**: Retrieve top 15, return best matches
- **Relevance Validation**: LLM-based result filtering

## Key Features

### Conversation Context
- **Message History**: Last 2 conversation turns used for context
- **State Persistence**: Conversation state maintained across interactions
- **Context Window Management**: Efficient token usage with sliding window

### Error Handling & Monitoring
- **Logfire Integration**: Comprehensive tracing and monitoring
- **Graceful Degradation**: Fallback responses when tools fail
- **Performance Tracking**: Agent response times and success rates
- **Error Recovery**: Automatic retry logic for transient failures

### Multi-Language Support
- **Russian Interface**: Primary user interface language
- **Korean Content**: Native Korean grammar explanations
- **Bilingual Responses**: Korean examples with Russian explanations

## Usage Patterns

### Agent Invocation
```python
# Router classification
router_result = await router_agent.run(
    user_prompt=message,
    output_type=RouterAgentResult,
    usage_limits=UsageLimits(request_limit=5)
)

# Thinking grammar response with RAG
thinking_result = await thinking_grammar_agent.run(
    user_prompt=message,
    deps=deps,
    message_history=history,
    usage_limits=UsageLimits(request_limit=5)
)
```

### Tool Integration
```python
# Grammar search with hybrid vector search
grammars = await retrieve_grammars_tool(deps, query, top_k=15)

# Document retrieval with HyDE enhancement
docs = await retrieve_docs_tool(deps, hypothetical_answer)
```

## Configuration
- **Model Selection**: Different GPT models optimized for each agent's role
- **Temperature Settings**: Zero for classification, higher for creative responses
- **Usage Limits**: Request limits to prevent excessive API usage
- **Embedding Models**: Configurable embedding models for different search types

## Performance Considerations
- **Model Efficiency**: GPT-4.1-mini for cost-effective longer responses
- **Caching**: Vector embeddings cached to reduce API calls
- **Async Operations**: All agents and tools are fully async
- **Resource Management**: Connection pooling and proper cleanup