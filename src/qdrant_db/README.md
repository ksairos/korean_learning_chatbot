# Qdrant DB Module

This module manages the vector database setup and data ingestion for Korean grammar content, enabling semantic search capabilities for the Korean Learning Bot.

## Core Features

- Creation and configuration of Qdrant vector collections
- Parsing of markdown grammar entries into structured JSON
- Generation of embeddings for grammar entries
- Uploading of grammar entries with embeddings to Qdrant
- Support for hybrid search (dense + sparse embeddings)

## Implementation Details

The module consists of two main components:

1. **create_qdrant_collection.py**: Sets up and populates the Qdrant collection
   - Creates collections with appropriate vector parameters
   - Configures sparse and dense vector indexes
   - Uploads grammar entries with embeddings to Qdrant
   - Supports both local and cloud Qdrant instances

2. **parse_md_to_json.py**: Parses markdown grammar entries to structured JSON
   - Extracts structured data from markdown files
   - Organizes grammar points with examples, meanings, and usage notes
   - Prepares data for vector embedding and database insertion

The Qdrant DB module enables efficient semantic search for Korean grammar concepts, allowing users to find relevant grammar explanations based on natural language queries rather than exact keyword matches.