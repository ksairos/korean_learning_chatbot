# Notebooks Package

## Purpose
Jupyter notebooks for data preprocessing, vector database setup, and exploratory data analysis for the Korean learning chatbot's grammar knowledge base.

## Key Components
- **create_qdrant_collection.ipynb**: Sets up Qdrant vector database collections and indexes grammar entries
- **preprocess_grammar_list.ipynb**: Processes raw grammar data and prepares it for embedding generation

## Functions
- **Data Preprocessing**: Cleans and structures Korean grammar entries from various sources
- **Vector Database Setup**: Creates Qdrant collections with proper configuration for semantic search
- **Embedding Generation**: Converts grammar entries to vector representations for similarity search
- **Data Validation**: Ensures grammar entries meet required schema standards

## Dependencies
- **src/qdrant_db/**: Vector database connection and operations
- **src/utils/**: Text processing and formatting utilities
- **data/**: Raw grammar data files and knowledge base sources

## Usage
Run notebooks for:
- Initial database setup and collection creation
- Grammar data preprocessing and cleaning
- Vector embedding generation and indexing
- Data exploration and quality assessment

## Integration
- **src/llm_agent/**: Uses processed grammar data for RAG functionality
- **src/qdrant_db/**: Populates vector database with processed entries
- **data/**: Sources raw grammar files for processing

## Output
- Populated Qdrant collections with grammar embeddings
- Cleaned and validated grammar entries in JSON format
- Vector indexes optimized for semantic similarity search
- Data quality reports and statistics