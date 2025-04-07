"""Import all routers and add them to routers_list."""
from .admin import admin_router
from .chat import chat_router
from .user import user_router
from .help import help_router
from .vocab import dictionary_router

routers_list = [
    admin_router,
    user_router,
    help_router,
    dictionary_router,
    chat_router,  # must be last
]

__all__ = [
    "routers_list",
]
