from typing import Any

from pydantic import computed_field, PostgresDsn
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

    # def construct_sqlalchemy_url(self, driver="asyncpg", host=None, port=None) -> str:
    #     """
    #     Constructs and returns a SQLAlchemy URL for this database configuration.
    #     """
    #     # TODO: If you're using SQLAlchemy, move the import to the top of the file!
    #     from sqlalchemy.engine.url import URL
    #
    #     if not host:
    #         host = self.host
    #     if not port:
    #         port = self.port
    #     uri = URL.create(
    #         drivername=f"postgresql+{driver}",
    #         username=self.user,
    #         password=self.password,Е
    #         host=host,
    #         port=port,
    #         database=self.database,
    #     )
    #     return uri.render_as_string(hide_password=False)
    
class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    qdrant_collection_name: str = "korean_grammar"
    qdrant_host: str = "localhost"
    qdrant_host_docker: str = "qdrant"
    qdrant_port: int = 6333

    bot_token: str | None = None
    admin_ids: list[int] | None = None
    use_redis: bool | None = None
    krdict_api_key: str | None = None

    logfire_api_key: str | None = None
    openai_api_key: str | None = None

    embedding_model: str = "text-embedding-3-small"
    sparse_embedding_model: str = 'Qdrant/bm25'
    reranking_model: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'

    postgres_host: str | None = None
    postgres_password: str | None = None
    postgres_user: str | None = None
    postgres_db: str | None = None
    postgres_port: int | None = None

    @computed_field
    @property
    def asyncpg_url(self) -> Any:
        """
           This is a computed field that generates a PostgresDsn URL for asyncpg.

           The URL is built using the MultiHostUrl.build method, which takes the following parameters:
           - scheme: The scheme of the URL. In this case, it is "postgresql+asyncpg".
           - username: The username for the Postgres database, retrieved from the POSTGRES_USER environment variable.
           - password: The password for the Postgres database, retrieved from the POSTGRES_PASSWORD environment variable.
           - host: The host of the Postgres database, retrieved from the POSTGRES_HOST environment variable.
           - path: The path of the Postgres database, retrieved from the POSTGRES_DB environment variable.

           Returns:
               PostgresDsn: The constructed PostgresDsn URL for asyncpg.
        """
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )
    
    # db: DbConfig = DbConfig()
    # redis: Optional[RedisConfig] = RedisConfig()

#TODO Implement redis if needed

# @dataclass
# class RedisConfig:
#     """
#     Redis configuration class.

#     Attributes
#     ----------
#     redis_pass : Optional(str)
#         The password used to authenticate with Redis.
#     redis_port : Optional(int)
#         The port where Redis server is listening.
#     redis_host : Optional(str)
#         The host where Redis server is located.
#     """

#     redis_pass: Optional[str]
#     redis_port: Optional[int]
#     redis_host: Optional[str]

#     def dsn(self) -> str:
#         """
#         Constructs and returns a Redis DSN (Data Source Name) for this database configuration.
#         """
#         if self.redis_pass:
#             return f"redis://:{self.redis_pass}@{self.redis_host}:{self.redis_port}/0"
#         else:
#             return f"redis://{self.redis_host}:{self.redis_port}/0"

#     @staticmethod
#     def from_env(env: Env):
#         """
#         Creates the RedisConfig object from environment variables.
#         """
#         redis_pass = env.str("REDIS_PASSWORD")
#         redis_port = env.int("REDIS_PORT")
#         redis_host = env.str("REDIS_HOST")

#         return RedisConfig(
#             redis_pass=redis_pass, redis_port=redis_port, redis_host=redis_host
#         )
    


# def load_config(path: str = None) -> Config:
#     """
#     This function takes an optional file path as input and returns a Config object.
#     :param path: The path of env file from where to load the configuration variables.
#     It reads environment variables from a .env file if provided, else from the process environment.
#     :return: Config object with attributes set as per environment variables.
#     """

#     # Create an Env object.
#     # The Env object will be used to read environment variables.
#     env = Env()
#     env.read_env(path)

#     return Config(
#         tg_bot=TgBot.from_env(env),
#         # db=DbConfig.from_env(env),
#         # redis=RedisConfig.from_env(env),
#         qdrant=QdrantConfig(),
#         misc=Miscellaneous(),
#     )