from aiogram.utils.keyboard import InlineKeyboardBuilder


def word_keyboard():
    # First, you should create an InlineKeyboardBuilder object
    keyboard = InlineKeyboardBuilder()

    # You can use the keyboard.button() method to add buttons, then enter text and callback_data
    keyboard.button(
        text="◀️ Пред. страница", callback_data="previous_word"
    )
    keyboard.button(
        text="След. страница ▶️", callback_data="next_word"
    )
    keyboard.button(
        text="Примеры 📝", callback_data="show_examples"
    )
    keyboard.button(
        text="Выйти 🚪", callback_data="exit_vocab_mode"
    )

    # If needed, you can use keyboard.adjust() method to change the number of buttons per row
    keyboard.adjust(2)

    # Then you should always call keyboard.as_markup() method to get a valid InlineKeyboardMarkup object
    return keyboard.as_markup()


def exit_keyboard():
    """Simple keyboard with only exit button"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Выйти из словаря 🚪", callback_data="exit_vocab_mode"
    )
    return keyboard.as_markup()


def examples_keyboard(current_page=0, total_pages=1):
    """
    Keyboard for navigating through example pages with a return button.

    Args:
        current_page: Current page number (0-based)
        total_pages: Total number of pages
    """
    keyboard = InlineKeyboardBuilder()

    # Add page navigation buttons
    keyboard.button(
        text="◀️ Пред. страница", callback_data="previous_page"
    )
    keyboard.button(
        text="След. страница ▶️", callback_data="next_page"
    )

    # Add return button
    keyboard.button(
        text="Назад к слову 🔙", callback_data="return_to_word"
    )

    # Add current page indicator
    keyboard.button(
        text=f"📄 {current_page + 1}/{total_pages}", callback_data="page_info"
    )
    
    # Add exit button
    keyboard.button(
        text="Выйти из словаря 🚪", callback_data="exit_vocab_mode"
    )

    keyboard.adjust(2)
    return keyboard.as_markup()