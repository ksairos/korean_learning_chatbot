# Korean Learning Bot - Dev Guidelines

## Commands
- **Run bot**: `docker compose up tgbot`
- **Run API**: `docker compose up api`
- **Run all services**: `docker compose up`
- **Linting**: `ruff check .`
- **DB migrations**: 
  - Apply: `alembic upgrade head`
  - Create: `alembic revision --autogenerate -m "message"`

## Code Style
- Use **type hints** for all function parameters and return values
- Follow **async/await** patterns consistently
- **Imports**: group std lib, 3rd party, local imports with blank line between
- **Error handling**: use try/except with specific exceptions, log with logfire
- **Naming**:
  - snake_case for variables, functions
  - CamelCase for classes
  - UPPER_CASE for constants
- Organize Telegram bot handlers by feature in separate modules
- Use Pydantic for data validation and settings
- Follow CRUD pattern for database operations
- Document complex functions with docstrings