from aiogram.fsm.state import State, StatesGroup


class VocabState(StatesGroup):
    """State for vocabulary dictionary mode."""
    active = State()  # User is in dictionary mode