# Qdrant Database Package

## Purpose
Manages Qdrant vector database operations for semantic search of Korean grammar entries. Provides RAG (Retrieval-Augmented Generation) capabilities for the LLM agent system.

## Key Components
- **qdrant_data/**: Local Qdrant database storage with collections and segments
- **collections/**: Contains grammar vector databases (`korean_grammar`, `korean_grammar_v2`)
- **segments/**: Vector storage partitions with payload and index data

## Database Structure
- **korean_grammar**: Original grammar collection with JSON-structured entries
- **korean_grammar_v2**: Updated collection with improved schema and embeddings
- **Vector embeddings**: Generated using OpenAI's `text-embedding-3-small` model
- **Payload storage**: Metadata and original text content for retrieved entries

## Dependencies
- **src/llm_agent/**: Provides semantic search functionality for agent tools
- **notebooks/**: Database setup and data ingestion scripts
- **src/utils/**: Text processing for embedding preparation

## Key Features
- Semantic similarity search for Korean grammar queries
- Hybrid search combining dense and sparse embeddings
- Reranking with CrossEncoder models for improved relevance
- Persistent storage with automatic indexing and optimization

## Usage
Database operations are accessed through:
- Client connection configured in `src/api/main.py`
- Search functions in `src/llm_agent/agent_tools.py`
- Collection management via notebooks

## Storage Layout
- **segments/**: Individual database partitions
- **payload_index/**: Metadata indexing for fast retrieval
- **vector_storage/**: Dense vector embeddings storage
- **wal/**: Write-ahead logging for transaction safety

## Configuration
- Host: Configurable for local development or Docker deployment
- Port: Default 6333 for Qdrant service
- Collections: Automatically created with proper vector dimensions and distance metrics