from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.config.settings import Config


class AdminFilter(BaseFilter):
    is_admin: bool = True

    async def __call__(self, obj: Message, config: Config) -> bool:
        return (obj.from_user.id in config.admin_ids) == self.is_admin
