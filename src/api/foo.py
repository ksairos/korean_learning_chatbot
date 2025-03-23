from src.config.settings import Config
from rich import print

config = Config()
print(config.model_dump_json)