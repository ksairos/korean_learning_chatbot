# Database Module

This module manages database models and data access for the Korean Learning Bot.

## Overview

The database package follows the repository pattern to abstract database operations. It provides a clean separation between database schema definition and data access logic.

## Key Components

### Models

- **models/base.py**: Base classes and mixins for all models
- **models/users.py**: User model definition

### Repositories

- **repo/base.py**: BaseRepo with session management
- **repo/users.py**: User-specific database operations
- **repo/requests.py**: Repository factory and coordination

### Setup

- **setup.py**: Database connection setup and session management

## Usage

### Accessing Repositories

```python
from infrastructure.database.repo.requests import RequestsRepo

async def use_db(session):
    # Get an instance of the requests repo for this session
    requests = RequestsRepo(session)
    
    # Access specific repositories
    user = await requests.users.get_user(user_id=123)
    
    # No need to commit - the session middleware handles transactions
    return user
```

### Creating Models

```python
from infrastructure.database.models.base import TimedBaseModel
from sqlalchemy import Column, String, Integer

class NewModel(TimedBaseModel):
    __tablename__ = "new_models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
```

### Adding a New Repository

1. Create a new repository file in repo/
2. Extend BaseRepo with model-specific operations
3. Add the repository to RequestsRepo

## Database Migrations

After changing models:
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Apply migration: `alembic upgrade head`

With Docker:
```bash
docker-compose exec api alembic upgrade head
```