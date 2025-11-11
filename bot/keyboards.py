"""Keyboard layouts for the bot."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Main menu keyboard for participants."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Программа"), KeyboardButton(text="🗓 Расписание")],
            [KeyboardButton(text="🎤 Спикеры"), KeyboardButton(text="🗺 Карта и схема")],
            [KeyboardButton(text="📺 Трансляция"), KeyboardButton(text="📝 Запись на активности")],
            [KeyboardButton(text="📋 Мои записи")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Admin menu keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Программа"), KeyboardButton(text="🗓 Расписание")],
            [KeyboardButton(text="🎤 Спикеры"), KeyboardButton(text="🗺 Карта и схема")],
            [KeyboardButton(text="📺 Трансляция"), KeyboardButton(text="📝 Запись на активности")],
            [KeyboardButton(text="📋 Мои записи")],
            [KeyboardButton(text="👑 Админ-панель")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Admin panel inline keyboard."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Рассылка уведомлений", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📊 Создать опрос", callback_data="admin_create_poll")],
            [InlineKeyboardButton(text="📝 Управление записями", callback_data="admin_bookings")],
            [InlineKeyboardButton(text="➕ Добавить активность", callback_data="admin_add_activity")],
            [InlineKeyboardButton(text="📋 Список участников", callback_data="admin_users_list")]
        ]
    )
    return keyboard


def get_speakers_keyboard(speakers: list) -> InlineKeyboardMarkup:
    """Keyboard with list of speakers."""
    buttons = []
    for speaker in speakers:
        buttons.append([InlineKeyboardButton(
            text=speaker['name'],
            callback_data=f"speaker_{speaker['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_activities_keyboard(activities: list, user_bookings: set = None) -> InlineKeyboardMarkup:
    """Keyboard with list of activities."""
    if user_bookings is None:
        user_bookings = set()

    buttons = []
    for activity in activities:
        # Check if user already booked this activity
        is_booked = activity['activity_id'] in user_bookings
        emoji = "✅" if is_booked else "📝"

        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {activity['name']}",
            callback_data=f"activity_{activity['activity_id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_activity_actions_keyboard(activity_id: int, is_booked: bool, is_full: bool) -> InlineKeyboardMarkup:
    """Keyboard for activity actions."""
    buttons = []

    if is_booked:
        buttons.append([InlineKeyboardButton(
            text="❌ Отменить запись",
            callback_data=f"cancel_{activity_id}"
        )])
    elif not is_full:
        buttons.append([InlineKeyboardButton(
            text="✅ Записаться",
            callback_data=f"book_{activity_id}"
        )])

    buttons.append([InlineKeyboardButton(
        text="🔙 Назад к списку",
        callback_data="back_to_activities"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_my_bookings_keyboard(bookings: list) -> InlineKeyboardMarkup:
    """Keyboard with user's bookings."""
    buttons = []
    for booking in bookings:
        buttons.append([InlineKeyboardButton(
            text=f"❌ {booking['name']}",
            callback_data=f"cancel_{booking['activity_id']}"
        )])

    if not buttons:
        buttons.append([InlineKeyboardButton(
            text="📝 Записаться на активности",
            callback_data="show_activities"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_activities_keyboard(activities: list) -> InlineKeyboardMarkup:
    """Admin keyboard for managing activities."""
    buttons = []
    for activity in activities:
        buttons.append([InlineKeyboardButton(
            text=activity['name'],
            callback_data=f"admin_activity_{activity['activity_id']}"
        )])
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_admin"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_activity_export_keyboard(activity_id: int) -> InlineKeyboardMarkup:
    """Keyboard for exporting activity bookings."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📥 Экспорт списка",
                callback_data=f"export_{activity_id}"
            )],
            [InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_bookings"
            )]
        ]
    )
    return keyboard


def get_poll_keyboard(poll_id: int, options: list) -> InlineKeyboardMarkup:
    """Keyboard for poll voting."""
    buttons = []
    for i, option in enumerate(options):
        buttons.append([InlineKeyboardButton(
            text=option,
            callback_data=f"vote_{poll_id}_{i}"
        )])
    buttons.append([InlineKeyboardButton(
        text="📊 Результаты",
        callback_data=f"poll_results_{poll_id}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel keyboard for multi-step operations."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
        ]
    )


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Back to admin panel button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
        ]
    )
