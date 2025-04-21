# TODO List for Korean Learning Bot

## Developer TODOs (Found in code)

### Database & User Management
- [ ] Automatically create chat in database when user starts the bot (`src/db/crud.py`)
- [ ] Handle adding new users to the database after `/start` command (`src/tgbot/handlers/user.py`)
- [ ] Implement proper connection pooling settings for database

### Grammar Features
- [ ] Add irregular verbs examples to grammar entries
- [ ] Update schema for irregular verbs in `src/schemas/schemas.py`
- [ ] Implement irregular verbs parsing in `src/qdrant_db/parse_md_to_json.py`

### API Improvements
- [ ] Replace standard Qdrant client with AsyncQdrantClient for better performance
- [ ] Implement the commented `rewrite_query` tool in `src/llm_agent/agent.py`

### System Configuration
- [ ] Configure Redis for storage if needed (`src/tgbot/bot.py`)
- [ ] Clean up commented SQLAlchemy URL construction code

### LLM Agent
- [ ] Implement grammar agent (currently commented out in `src/llm_agent/agent.py`)
- [ ] Upgrade translation model as suggested in router prompt
- [ ] Enhance cross-encoder to work with more than just description

## Senior Developer Recommendations

### Code Quality & Architecture
- [ ] Add comprehensive unit tests for all modules
- [ ] Implement consistent error handling across the application
- [ ] Add logging for monitoring and debugging
- [ ] Standardize docstring format across all modules
- [ ] Add type hints to all functions and methods

### Performance & Scalability
- [ ] Implement caching for frequently accessed grammar points
- [ ] Add rate limiting for Telegram API and OpenAI API
- [ ] Implement background tasks for non-critical operations
- [ ] Add health check endpoints to the API
- [ ] Set up monitoring and alerting

### Features & Enhancements
- [ ] Add spaced repetition system for vocabulary learning
- [ ] Implement user progress tracking
- [ ] Add pronunciation feedback using speech recognition
- [ ] Develop guided lessons with progressive difficulty
- [ ] Create a user settings menu for customization
- [ ] Implement multi-language support (beyond Russian)
- [ ] Add conversation practice mode with realistic scenarios

### Security & Deployment
- [ ] Implement proper secrets management
- [ ] Add input validation for all user inputs
- [ ] Set up CI/CD pipeline for automated testing and deployment
- [ ] Create backup and restore procedures for database and vector data
- [ ] Implement proper logging with PII protection

### Documentation
- [ ] Create comprehensive API documentation
- [ ] Add sequence diagrams for key workflows
- [ ] Document the conversation state machine
- [ ] Create user guide for bot commands and features