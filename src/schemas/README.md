# Schemas Module

This module defines data schemas used throughout the Korean Learning Bot application for data validation, serialization, and type safety.

## Core Features

- Pydantic models for request and response validation
- Type definitions for agent inputs and outputs
- Structured data schemas for grammar entries and search results
- Models for Telegram messages and user data

## Implementation Details

The module provides Pydantic models that define the structure of:

1. **Agent Dependencies**:
   - RouterDependencies: Configuration for the router agent
   - TranslationDependencies: Configuration for the translation agent
   - GrammarDependencies: Configuration for the grammar agent

2. **Data Structures**:
   - GrammarEntry: Schema for Korean grammar points
   - RetrievalResult: Structure for vector search results
   - TelegramMessage: Schema for Telegram message data
   - UserMessage: Structured user input data

3. **Result Models**:
   - RouterResult: Output from the router agent
   - TranslationResult: Output from the translation agent
   - GrammarResult: Output from the grammar agent

These schemas ensure data consistency across the application and provide type safety for function parameters and return values. They also enable automatic validation of incoming and outgoing data.