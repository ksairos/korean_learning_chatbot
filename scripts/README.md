# Helper Scripts Module

This module contains utility scripts for development and deployment operations.

## Overview

These scripts simplify common development tasks through simple shell commands, making database management and other operations more accessible.

## Key Components

### Alembic Database Migration Scripts

- **alembic/create_alembic.sh**: Initializes Alembic configuration
- **alembic/create_migrations.sh**: Creates new migration revisions
- **alembic/run_migrations.sh**: Applies pending migrations

### PostgreSQL Management Scripts

- **postgres/create_dump.sh**: Creates database backups

## Usage

### Database Migrations

Initialize Alembic (first time only):
```bash
./scripts/alembic/create_alembic.sh
```

Create a new migration after model changes:
```bash
./scripts/alembic/create_migrations.sh "description_of_changes"
```

Apply pending migrations:
```bash
./scripts/alembic/run_migrations.sh
```

With Docker Compose:
```bash
docker-compose exec api alembic upgrade head
```

### Database Backups

Create a database backup:
```bash
./scripts/postgres/create_dump.sh
```

## Adding New Scripts

When adding new scripts:
1. Create a new subdirectory for the category if needed
2. Ensure the script has proper execute permissions (`chmod +x`)
3. Include descriptive comments at the top of the script
4. Add the script to this README