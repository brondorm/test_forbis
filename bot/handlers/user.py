"""User handlers for main menu functions."""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.config import (
    EVENT_PROGRAM, EVENT_SCHEDULE, SPEAKERS, STREAM_URL,
    MAP_IMAGE_PATH, ADMIN_IDS
)
from bot.keyboards import (
    get_main_menu, get_admin_menu, get_speakers_keyboard
)
from bot.database import Database
import os

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Start command handler."""
    user = message.from_user
    is_admin = user.id in ADMIN_IDS

    # Register user in database
    await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=is_admin
    )

    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

Это бот конференции. Здесь вы можете:
• Посмотреть программу и расписание
• Узнать о спикерах
• Записаться на активности
• Получить карту мероприятия
• Посмотреть трансляцию

Используйте меню ниже для навигации.
"""

    keyboard = get_admin_menu() if is_admin else get_main_menu()
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(F.text == "📋 Программа")
async def show_program(message: Message):
    """Show event program."""
    await message.answer(EVENT_PROGRAM, parse_mode="Markdown")


@router.message(F.text == "🗓 Расписание")
async def show_schedule(message: Message):
    """Show event schedule."""
    await message.answer(EVENT_SCHEDULE, parse_mode="Markdown")


@router.message(F.text == "🎤 Спикеры")
async def show_speakers(message: Message):
    """Show list of speakers."""
    keyboard = get_speakers_keyboard(SPEAKERS)
    await message.answer(
        "🎤 **Спикеры конференции**\n\nВыберите спикера для просмотра информации:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("speaker_"))
async def show_speaker_info(callback: CallbackQuery):
    """Show speaker information."""
    speaker_id = int(callback.data.split("_")[1])
    speaker = next((s for s in SPEAKERS if s['id'] == speaker_id), None)

    if not speaker:
        await callback.answer("Спикер не найден", show_alert=True)
        return

    info_text = f"""
🎤 **{speaker['name']}**

📌 {speaker['title']}

📝 {speaker['bio']}
"""

    if speaker['photo']:
        # If photo file_id is stored
        await callback.message.answer_photo(
            photo=speaker['photo'],
            caption=info_text,
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(info_text, parse_mode="Markdown")

    await callback.answer()


@router.message(F.text == "🗺 Карта и схема")
async def show_map(message: Message):
    """Show event map."""
    # Check if map image exists
    if os.path.exists(MAP_IMAGE_PATH):
        photo = FSInputFile(MAP_IMAGE_PATH)
        await message.answer_photo(
            photo=photo,
            caption="🗺 Карта мероприятия"
        )
    else:
        await message.answer(
            "🗺 **Карта мероприятия**\n\n"
            "📍 Адрес: Конференц-центр \"Сколково\"\n"
            "🏢 Этаж: 3\n"
            "🚪 Залы: A, B, C\n\n"
            "ℹ️ Карта будет доступна позже.",
            parse_mode="Markdown"
        )


@router.message(F.text == "📺 Трансляция")
async def show_stream(message: Message):
    """Show stream link."""
    await message.answer(
        f"📺 **Прямая трансляция**\n\n"
        f"Смотрите трансляцию конференции:\n{STREAM_URL}",
        parse_mode="Markdown"
    )
