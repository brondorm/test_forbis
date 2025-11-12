"""Admin handlers for management functions."""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.filters import StateFilter
import logging

from bot.config import ADMIN_IDS, MAX_BOOKING_CAPACITY
from bot.database import Database
from bot.keyboards import (
    get_admin_panel_keyboard,
    get_admin_activities_keyboard,
    get_activity_export_keyboard,
    get_cancel_keyboard,
    get_back_to_admin_keyboard
)
import csv
from io import StringIO

logger = logging.getLogger(__name__)
router = Router()
# Navigation router with higher priority - registered first
nav_router = Router()


class AdminStates(StatesGroup):
    """States for admin operations."""
    waiting_broadcast_message = State()
    waiting_activity_name = State()
    waiting_activity_description = State()
    waiting_activity_datetime = State()
    waiting_activity_capacity = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in ADMIN_IDS


@router.message(F.text == "👑 Админ-панель")
async def show_admin_panel(message: Message):
    """Show admin panel."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели")
        return

    text = """
👑 **Админ-панель**

Выберите действие:
"""
    keyboard = get_admin_panel_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@nav_router.callback_query(
    F.data == "back_to_admin",
    StateFilter(None, AdminStates.waiting_broadcast_message, AdminStates.waiting_activity_name,
                AdminStates.waiting_activity_description, AdminStates.waiting_activity_datetime,
                AdminStates.waiting_activity_capacity)
)
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    """Return to admin panel."""
    logger.info(f"Back to admin called by user {callback.from_user.id}")
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    await state.clear()
    logger.info("State cleared, returning to admin panel")

    text = """
👑 **Админ-панель**

Выберите действие:
"""
    keyboard = get_admin_panel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


# Broadcast functionality
@router.callback_query(F.data == "admin_broadcast", StateFilter("*"))
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast message creation."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_broadcast_message)

    text = """
📢 **Рассылка уведомлений**

Отправьте сообщение, которое будет разослано всем участникам.

Вы можете отправить:
• Текст
• Фото с подписью
• Видео с подписью

Для отмены используйте кнопку ниже.
"""
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_message)
async def process_broadcast(message: Message, state: FSMContext, db: Database, bot: Bot):
    """Process and send broadcast message."""
    if not is_admin(message.from_user.id):
        return

    # Get all users
    users = await db.get_all_users()

    await message.answer(f"📤 Начинаю рассылку для {len(users)} пользователей...")

    success_count = 0
    failed_count = 0

    for user in users:
        try:
            # Forward the message to each user
            await message.copy_to(chat_id=user['user_id'])
            success_count += 1
        except Exception as e:
            failed_count += 1

    await state.clear()

    result_text = f"""
✅ **Рассылка завершена**

Успешно: {success_count}
Ошибок: {failed_count}
"""
    keyboard = get_back_to_admin_keyboard()
    await message.answer(result_text, reply_markup=keyboard, parse_mode="Markdown")


# Activity management
@router.callback_query(F.data == "admin_add_activity", StateFilter("*"))
async def start_add_activity(callback: CallbackQuery, state: FSMContext):
    """Start adding new activity."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_activity_name)

    text = """
➕ **Добавление активности**

Шаг 1/4: Введите название активности
"""
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.message(AdminStates.waiting_activity_name)
async def process_activity_name(message: Message, state: FSMContext):
    """Process activity name."""
    if not is_admin(message.from_user.id):
        return

    await state.update_data(activity_name=message.text)
    await state.set_state(AdminStates.waiting_activity_description)

    text = """
➕ **Добавление активности**

Шаг 2/4: Введите описание активности
"""
    keyboard = get_cancel_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(AdminStates.waiting_activity_description)
async def process_activity_description(message: Message, state: FSMContext):
    """Process activity description."""
    if not is_admin(message.from_user.id):
        return

    await state.update_data(activity_description=message.text)
    await state.set_state(AdminStates.waiting_activity_datetime)

    text = """
➕ **Добавление активности**

Шаг 3/4: Введите дату и время (например: 15 ноября, 14:00)
"""
    keyboard = get_cancel_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(AdminStates.waiting_activity_datetime)
async def process_activity_datetime(message: Message, state: FSMContext):
    """Process activity datetime."""
    if not is_admin(message.from_user.id):
        return

    await state.update_data(activity_datetime=message.text)
    await state.set_state(AdminStates.waiting_activity_capacity)

    text = f"""
➕ **Добавление активности**

Шаг 4/4: Введите максимальное количество участников
(по умолчанию: {MAX_BOOKING_CAPACITY})

Или отправьте "-" для использования значения по умолчанию.
"""
    keyboard = get_cancel_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(AdminStates.waiting_activity_capacity)
async def process_activity_capacity(message: Message, state: FSMContext, db: Database):
    """Process activity capacity and create activity."""
    if not is_admin(message.from_user.id):
        return

    # Parse capacity
    if message.text.strip() == "-":
        capacity = MAX_BOOKING_CAPACITY
    else:
        try:
            capacity = int(message.text)
            if capacity <= 0:
                await message.answer("⚠️ Количество должно быть положительным числом. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("⚠️ Введите корректное число или '-'. Попробуйте снова:")
            return

    # Get all data
    data = await state.get_data()

    # Create activity
    activity_id = await db.add_activity(
        name=data['activity_name'],
        description=data['activity_description'],
        date_time=data['activity_datetime'],
        max_capacity=capacity
    )

    await state.clear()

    text = f"""
✅ **Активность создана**

📝 {data['activity_name']}
📅 {data['activity_datetime']}
👥 Лимит: {capacity} человек
"""
    keyboard = get_back_to_admin_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# Booking management
@router.callback_query(F.data == "admin_bookings", StateFilter("*"))
async def show_admin_bookings(callback: CallbackQuery, db: Database, state: FSMContext):
    """Show activities for booking management."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    # Clear any active state
    await state.clear()

    activities = await db.get_activities()

    if not activities:
        text = "📝 Нет доступных активностей"
        keyboard = get_back_to_admin_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return

    text = """
📝 **Управление записями**

Выберите активность для просмотра списка записавшихся:
"""
    keyboard = get_admin_activities_keyboard(activities)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_activity_"))
async def show_activity_bookings(callback: CallbackQuery, db: Database):
    """Show bookings for specific activity."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    activity_id = int(callback.data.split("_")[2])

    activity = await db.get_activity(activity_id)
    bookings = await db.get_activity_bookings(activity_id)

    text = f"""
📝 **{activity['name']}**

👥 Записано: {len(bookings)}/{activity['max_capacity']}

**Список участников:**
"""

    if bookings:
        for i, booking in enumerate(bookings, 1):
            name = booking['first_name'] or ""
            last_name = booking['last_name'] or ""
            username = f"@{booking['username']}" if booking['username'] else ""
            text += f"\n{i}. {name} {last_name} {username}"
    else:
        text += "\n_Пока никто не записался_"

    keyboard = get_activity_export_keyboard(activity_id)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("export_"))
async def export_bookings(callback: CallbackQuery, db: Database):
    """Export bookings to CSV."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    activity_id = int(callback.data.split("_")[1])

    activity = await db.get_activity(activity_id)
    bookings = await db.get_activity_bookings(activity_id)

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['№', 'Имя', 'Фамилия', 'Username', 'User ID', 'Дата записи'])

    # Data
    for i, booking in enumerate(bookings, 1):
        writer.writerow([
            i,
            booking['first_name'] or '',
            booking['last_name'] or '',
            booking['username'] or '',
            booking['user_id'],
            booking['booked_at']
        ])

    # Send file
    csv_content = output.getvalue()
    file = BufferedInputFile(
        csv_content.encode('utf-8-sig'),  # BOM for Excel compatibility
        filename=f"bookings_{activity['name']}.csv"
    )

    await callback.message.answer_document(
        document=file,
        caption=f"📥 Экспорт записей для активности \"{activity['name']}\"\n"
                f"Всего записей: {len(bookings)}"
    )

    await callback.answer("✅ Файл отправлен")


# Users list
@router.callback_query(F.data == "admin_users_list", StateFilter("*"))
async def show_users_list(callback: CallbackQuery, db: Database, state: FSMContext):
    """Show list of all registered users."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    # Clear any active state
    await state.clear()

    users = await db.get_all_users()

    text = f"""
👥 **Список участников**

Всего зарегистрировано: {len(users)}

"""

    for i, user in enumerate(users[:50], 1):  # Limit to 50 for message length
        name = user['first_name'] or ""
        username = f"@{user['username']}" if user['username'] else ""
        text += f"{i}. {name} {username}\n"

    if len(users) > 50:
        text += f"\n... и еще {len(users) - 50} участников"

    keyboard = get_back_to_admin_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


# Cancel operation
@nav_router.callback_query(
    F.data == "cancel_operation",
    StateFilter(
        None,  # No state
        AdminStates.waiting_broadcast_message,
        AdminStates.waiting_activity_name,
        AdminStates.waiting_activity_description,
        AdminStates.waiting_activity_datetime,
        AdminStates.waiting_activity_capacity,
        "PollStates:waiting_question",  # Poll states as strings
        "PollStates:waiting_options"
    )
)
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Cancel current operation and return to admin panel."""
    logger.info(f"Cancel operation called by user {callback.from_user.id}")

    if not is_admin(callback.from_user.id):
        logger.warning(f"Non-admin user {callback.from_user.id} tried to cancel operation")
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    current_state = await state.get_state()
    logger.info(f"Clearing state: {current_state}")
    await state.clear()

    text = """
👑 **Админ-панель**

Выберите действие:
"""
    keyboard = get_admin_panel_keyboard()

    try:
        logger.info("Attempting to edit message")
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer("❌ Операция отменена")
        logger.info("Successfully returned to admin panel")
    except Exception as e:
        logger.error(f"Error editing message: {e}", exc_info=True)
        await callback.answer("❌ Операция отменена")
        # Try sending new message if edit fails
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
