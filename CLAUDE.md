# Korean Learning Bot - Development Guide

## Commands
- **Run bot locally**: `python -m tgbot.bot` or `python main.py`
- **Install deps**: `uv pip install -r requirements.txt` (preferred) or `pip install -r requirements.txt`
- **Docker setup**: `docker compose up --build` (use `-d` for detached mode)

## Testing & Linting
- **Run tests**: `pytest tests/`
- **Run single test**: `pytest tests/path_to_test.py::test_function_name -v`
- **Debug test**: `pytest tests/path_to_test.py -vvs`
- **Lint code**: `flake8 .`
- **Type check**: `mypy .`
- **Format code**: `black .`

## Code Style
- **Imports**: Group as standard lib → third-party → local, alphabetically within groups
- **Formatting**: 
  - Docstrings for all functions/classes ("""Summary line. Detailed description.""")
  - Line length: 88 characters max (Black compatible)
- **Types**: Use type hints for parameters and return values (Python 3.12+ syntax)
- **Naming**: 
  - snake_case for variables/functions
  - CamelCase for classes
  - ALL_CAPS for constants
- **Error handling**: Use specific exceptions with contextual messages
- **Telegram Bot**: 
  - Register all routers in tgbot/handlers/__init__.py (echo_router must be last)
  - All handlers must be async functions with proper type annotations
  - Use FSM for multi-step operations via Redis storage
- **Commits**: Use descriptive commit messages with present tense verbs

## Project Structure
- **tgbot/**: Telegram bot using aiogram 3.x
- **api/**: FastAPI backend endpoints
- **scripts/**: Utility scripts for DB and deployment operations
- Environment variables in `.env` file (see README.md for required variables)