"""Import all routers and add them to routers_list."""
from .admin import admin_router
from .echo import echo_router
from .simple_menu import menu_router
from .user import user_router
from .help import help_router
from .api_integration import api_router  # Import our new router

routers_list = [
    admin_router,
    menu_router,
    user_router,
    help_router,
    api_router,  # Add it before echo_router
    echo_router,  # echo_router must be last
]

__all__ = [
    "routers_list",
]
