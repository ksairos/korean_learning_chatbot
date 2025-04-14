from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.config.settings import Config

config = Config()

SQLALCHEMY_DATABASE_URI = URL.create(
    drivername="postgresql+psycopg",
    username=config.db_username,
    password=config.db_password,
    host=config.db_host,
    database=config.db_name,
    port=config.db_port,
)

engine = create_engine(SQLALCHEMY_DATABASE_URI)
session_local = sessionmaker(autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    database = session_local()
    try:
        yield database
    finally:
        database.close()