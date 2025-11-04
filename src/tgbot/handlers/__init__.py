"""Import all routers and add them to routers_list."""
from .admin import admin_router
from .chat import chat_router
from .user import user_router
from .translation_mode import translation_router
from .conversation_mode import conversation_router

routers_list = [
    admin_router,
    user_router,
    translation_router,
    conversation_router,
    chat_router,  # must be last
]

__all__ = [
    "routers_list",
]
