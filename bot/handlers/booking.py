"""Booking handlers for activity registration."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from typing import Union

from bot.database import Database
from bot.keyboards import (
    get_activities_keyboard,
    get_activity_actions_keyboard,
    get_my_bookings_keyboard
)

router = Router()


@router.message(F.text == "📝 Запись на активности")
@router.callback_query(F.data == "show_activities")
@router.callback_query(F.data == "back_to_activities")
async def show_activities(event: Union[Message, CallbackQuery], db: Database):
    """Show list of activities for booking."""
    user_id = event.from_user.id

    # Get all active activities
    activities = await db.get_activities(active_only=True)

    if not activities:
        text = "📝 В данный момент нет доступных активностей для записи."
        if isinstance(event, CallbackQuery):
            await event.message.answer(text)
            await event.answer()
        else:
            await event.answer(text)
        return

    # Get user's bookings
    user_bookings = await db.get_user_bookings(user_id)
    booked_ids = {b['activity_id'] for b in user_bookings}

    keyboard = get_activities_keyboard(activities, booked_ids)

    text = "📝 **Доступные активности**\n\n" \
           "Выберите активность для записи или просмотра информации:\n\n" \
           "✅ - вы уже записаны\n" \
           "📝 - доступно для записи"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data.startswith("activity_"))
async def show_activity_details(callback: CallbackQuery, db: Database):
    """Show activity details and booking options."""
    activity_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    # Get activity info
    activity = await db.get_activity(activity_id)
    if not activity:
        await callback.answer("Активность не найдена", show_alert=True)
        return

    # Check if user already booked
    is_booked = await db.is_user_booked(user_id, activity_id)

    # Get current booking count
    booking_count = await db.get_booking_count(activity_id)
    max_capacity = activity['max_capacity']
    is_full = booking_count >= max_capacity

    # Prepare message
    status_emoji = "✅" if is_booked else ("❌" if is_full else "📝")

    text = f"""
{status_emoji} **{activity['name']}**

📝 {activity['description']}

📅 {activity['date_time']}

👥 Записано: {booking_count}/{max_capacity}
"""

    if is_booked:
        text += "\n✅ Вы записаны на эту активность"
    elif is_full:
        text += "\n❌ Все места заняты"
    else:
        text += f"\n📝 Свободно мест: {max_capacity - booking_count}"

    keyboard = get_activity_actions_keyboard(activity_id, is_booked, is_full)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("book_"))
async def book_activity(callback: CallbackQuery, db: Database):
    """Book an activity."""
    activity_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    # Try to create booking
    success = await db.create_booking(user_id, activity_id)

    if success:
        await callback.answer("✅ Вы успешно записаны!", show_alert=True)

        # Refresh activity details
        await show_activity_details(
            CallbackQuery(
                id=callback.id,
                from_user=callback.from_user,
                message=callback.message,
                chat_instance=callback.chat_instance,
                data=f"activity_{activity_id}"
            ),
            db
        )
    else:
        # Check why booking failed
        is_booked = await db.is_user_booked(user_id, activity_id)
        if is_booked:
            await callback.answer("⚠️ Вы уже записаны на эту активность", show_alert=True)
        else:
            await callback.answer("❌ Все места заняты", show_alert=True)


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_booking(callback: CallbackQuery, db: Database):
    """Cancel a booking."""
    # Extract activity_id from callback data
    parts = callback.data.split("_")
    if len(parts) < 2:
        return

    # Check if the second part is a valid number (activity_id)
    try:
        activity_id = int(parts[1])
    except ValueError:
        # Not a booking cancellation, skip this handler
        return

    user_id = callback.from_user.id

    # Cancel booking
    success = await db.cancel_booking(user_id, activity_id)

    if success:
        await callback.answer("✅ Запись отменена", show_alert=True)

        # Try to refresh activity details if we're on activity page
        if callback.message and "Записано:" in callback.message.text:
            await show_activity_details(
                CallbackQuery(
                    id=callback.id,
                    from_user=callback.from_user,
                    message=callback.message,
                    chat_instance=callback.chat_instance,
                    data=f"activity_{activity_id}"
                ),
                db
            )
        else:
            # Refresh bookings list
            await show_my_bookings(callback, db)
    else:
        await callback.answer("⚠️ Не удалось отменить запись", show_alert=True)


@router.message(F.text == "📋 Мои записи")
async def show_my_bookings(event: Union[Message, CallbackQuery], db: Database):
    """Show user's bookings."""
    user_id = event.from_user.id

    # Get user's bookings
    bookings = await db.get_user_bookings(user_id)

    if not bookings:
        text = "📋 У вас пока нет записей на активности.\n\n" \
               "Используйте кнопку \"📝 Запись на активности\" для записи."

        if isinstance(event, CallbackQuery):
            await event.message.answer(text)
            await event.answer()
        else:
            await event.answer(text)
        return

    text = "📋 **Ваши записи**\n\n"
    for booking in bookings:
        text += f"✅ **{booking['name']}**\n"
        text += f"   📅 {booking['date_time']}\n\n"

    text += "\nДля отмены записи нажмите на соответствующую активность:"

    keyboard = get_my_bookings_keyboard(bookings)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="Markdown")
