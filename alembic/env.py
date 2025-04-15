import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from src.config.settings import Config
from src.db.models import Base

config = Config()

target_metadata = Base.metadata


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = config.asyncpg_url.unicode_string()
    connectable = create_async_engine(
        url, future=True
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

if context.is_offline_mode():
    # Typically, offline mode needs a different approach, but if you don’t require it,
    # you can raise an exception or implement a compatible solution.
    raise NotImplementedError("Offline migrations are not currently supported with async engines")
else:
    asyncio.run(run_migrations_online())
