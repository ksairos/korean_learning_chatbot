# Config Module

This module centralizes all configuration settings and prompt templates for the Korean Learning Bot application.

## Core Features

- Environment variables management using Pydantic settings
- Database connection string configuration
- LLM system prompt templates for different agent types
- Vector database and embedding configuration
- API credential management

## Implementation Details

The module consists of two main components:

1. **settings.py**: Defines application settings and environment variables using Pydantic BaseSettings
   - Database connection parameters
   - Bot configuration
   - OpenAI API settings
   - Qdrant vector DB configuration

2. **prompts.py**: Contains system prompts for the LLM agents
   - Router agent prompts for message classification
   - Translation agent prompts
   - Grammar agent prompts
   - Formatting templates for responses

These configuration files serve as a central reference point for application settings, ensuring consistent configuration across all modules.