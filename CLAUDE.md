# Korean Learning Bot - Development Guide

## Commands
- **Run bot**: `python3 bot.py`
- **Install dependencies**: `pip install -r requirements.txt --pre`
- **Docker run**: `docker-compose up --build`
- **Database migrations**: `docker-compose exec api alembic upgrade head`
- **Create migration**: Scripts in `scripts/alembic/`

## Code Style
- **Imports**: Group by standard lib → third-party → local, alphabetically within groups
- **Formatting**: Use docstrings for functions (see bot.py examples)
- **Types**: Type hints for function parameters and return values
- **Naming**: 
  - snake_case for variables/functions
  - CamelCase for classes
  - ALL_CAPS for constants
- **Error handling**: Use try/except blocks with specific exceptions
- **Structure**: Follow aiogram handler/router organization pattern
- **Handler registration**: Add routers to tgbot/handlers/__init__.py
- **Async**: All handlers should be async functions

## Architecture
- aiogram v3.0+ with SQLAlchemy 2.0 and Alembic for migrations
- Configuration using environs from .env file
- Redis optional for FSM storage