# Korean Learning Bot - Development Guide

## Commands
- **Run bot**: `python bot.py` or `python main.py`
- **Install dependencies**: `pip install -r requirements.txt`
- **Docker setup**: `docker-compose up --build`
- **Database migrations**: 
  - Run migrations: `docker-compose exec api alembic upgrade head`
  - Create migration: `./scripts/alembic/create_migrations.sh "migration_description"`
  - Run locally: `alembic upgrade head`

## Testing & Linting
- **Run tests**: `pytest tests/`
- **Run single test**: `pytest tests/path_to_test.py::test_function_name -v`
- **Lint code**: `flake8 .`
- **Type check**: `mypy .`

## Code Style
- **Imports**: Group as standard lib → third-party → local, alphabetically within groups
- **Formatting**: Use docstrings for all functions and classes
- **Types**: Always use type hints for parameters and return values
- **Naming**: 
  - snake_case for variables/functions
  - CamelCase for classes
  - ALL_CAPS for constants
- **Error handling**: Use specific exceptions in try/except blocks
- **Telegram Bot**: 
  - Register handlers in tgbot/handlers/__init__.py
  - All handlers must be async functions
  - Keep router organization consistent with aiogram patterns

## Architecture
- aiogram v3.0+ with SQLAlchemy 2.0 and Alembic for migrations
- Configuration via .env file using environs package
- Redis for FSM storage
- RAG system integration for chatbot functionality