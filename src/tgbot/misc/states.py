from aiogram.fsm.state import State, StatesGroup


class VocabState(StatesGroup):
    """State for vocabulary dictionary mode."""
    active = State()  # User is in dictionary mode


class TranslationState(StatesGroup):
    """State for translation mode."""
    active = State()  # User is in translation mode


class ConversationState(StatesGroup):
    """State for conversation mode."""
    active = State()  # User is in conversation mode


class LearningState(StatesGroup):
    """State for learning practice"""
    active = State()
    turn_count = State()