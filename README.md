# Korean Learning Bot

This project is a Telegram bot designed for Korean language learning, built with aiogram, FastAPI, PostgreSQL, and Redis, all containerized with Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- A Telegram Bot Token (obtainable from [BotFather](https://t.me/BotFather))
- Basic understanding of Python and Docker

## Environment Setup

1. Create a `.env` file in the root directory with the following variables:

```
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token
ADMINS=123456789,987654321  # Comma-separated Telegram user IDs
USE_REDIS=true

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=korean_bot
DB_HOST=postgres
DB_PORT=5432

# Redis Configuration
REDIS_PASSWORD=redis_password
REDIS_HOST=redis
REDIS_PORT=6379
```

## Building and Running the Project

1. **Build and start all services**:
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode**:
   ```bash
   docker-compose up -d
   ```

3. **Apply database migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

4. **Create new migrations**:
   ```bash
   ./scripts/alembic/create_migrations.sh "migration description"
   ```

## Project Architecture

The project consists of several interconnected services:

1. **Telegram Bot** (`bot` service)
   - Built with aiogram 3.0+
   - Handles all Telegram interactions
   - Communicates with API service

2. **FastAPI Backend** (`api` service)
   - Provides HTTP API endpoints
   - Exposes webhook endpoint for Telegram
   - Runs on port 8000

3. **PostgreSQL Database** (`postgres` service)
   - Stores user data, conversation history
   - Accessible on port 5432

4. **Redis** (`redis` service)
   - Used for FSM (Finite State Machine) storage
   - Caches frequently accessed data

5. **Nginx** (`nginx` service)
   - Provides reverse proxy
   - Handles SSL termination
   - Exposes ports 80 and 443

## Integration Between Telegram Bot and FastAPI

The system works with these connections:

1. **Bot to API**:
   - The Telegram bot communicates with the FastAPI service over the network
   - The bot service depends on the API service (see `depends_on` in docker-compose.yml)

2. **API to Telegram**:
   - The FastAPI app initializes a Bot instance using your Telegram token
   - Example endpoint in `infrastructure/api/app.py`:
     ```python
     @app.post("/api")
     async def webhook_endpoint(request: fastapi.Request):
         return JSONResponse(status_code=200, content={"status": "ok"})
     ```

3. **Data Flow**:
   - User sends message to Telegram bot
   - Bot processes message and may send requests to API
   - API may interact with database/external services
   - Response flows back to user via bot

## Troubleshooting

### Common Issues:

1. **Bot doesn't respond**:
   - Check if the BOT_TOKEN is correct
   - Ensure the bot service is running: `docker-compose ps`
   - Check logs: `docker-compose logs bot`

2. **Database connection issues**:
   - Verify PostgreSQL is running: `docker-compose ps postgres`
   - Check environment variables in .env match docker-compose.yml
   - Review logs: `docker-compose logs postgres`

3. **API service fails to start**:
   - Check if required dependencies are installed
   - Review logs: `docker-compose logs api`
   - Ensure PostgreSQL is running and accessible

4. **Redis connection issues**:
   - Verify Redis is running: `docker-compose ps redis`
   - Check Redis configuration in .env
   - Review logs: `docker-compose logs redis`

5. **Fixing container issues**:
   - Restart services: `docker-compose restart <service_name>`
   - Rebuild a specific service: `docker-compose up -d --build <service_name>`
   - Check all logs: `docker-compose logs --tail=100`

## Creating and Registering Handlers

1. **Create a new module** `your_name.py` inside the `handlers` folder.
2. **Define a router** in `your_name.py`:
   ```python
   from aiogram import Router
   user_router = Router()
   ```
3. **You can create multiple routers** in the same module and attach handlers to each.
4. **Register handlers using decorators**:
   ```python
   @user_router.message(commands=["start"])
   async def user_start(message):
       await message.reply("Welcome, regular user!")
   ```
5. **Add routers to `handlers/__init__.py`**:
   ```python
   from .admin import admin_router
   from .echo import echo_router
   from .user import user_router

   routers_list = [
       admin_router,
       user_router,
       echo_router,  # echo_router must be last
   ]
   ```

For more details on development practices, code style, and architecture, refer to [CLAUDE.md](./CLAUDE.md).