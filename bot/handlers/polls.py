"""Poll handlers for creating and managing polls."""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import ADMIN_IDS
from bot.database import Database
from bot.keyboards import (
    get_poll_keyboard,
    get_cancel_keyboard,
    get_back_to_admin_keyboard
)

router = Router()


class PollStates(StatesGroup):
    """States for poll creation."""
    waiting_question = State()
    waiting_options = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in ADMIN_IDS


@router.callback_query(F.data == "admin_create_poll")
async def start_create_poll(callback: CallbackQuery, state: FSMContext):
    """Start poll creation."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    await state.set_state(PollStates.waiting_question)

    text = """
📊 **Создание опроса**

Шаг 1/2: Введите вопрос опроса
"""
    keyboard = get_cancel_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.message(PollStates.waiting_question)
async def process_poll_question(message: Message, state: FSMContext):
    """Process poll question."""
    if not is_admin(message.from_user.id):
        return

    await state.update_data(poll_question=message.text)
    await state.set_state(PollStates.waiting_options)

    text = """
📊 **Создание опроса**

Шаг 2/2: Введите варианты ответов

Каждый вариант с новой строки, например:
```
Вариант 1
Вариант 2
Вариант 3
```

Минимум 2 варианта.
"""
    keyboard = get_cancel_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(PollStates.waiting_options)
async def process_poll_options(message: Message, state: FSMContext, db: Database, bot: Bot):
    """Process poll options and create poll."""
    if not is_admin(message.from_user.id):
        return

    # Parse options
    options = [opt.strip() for opt in message.text.split('\n') if opt.strip()]

    if len(options) < 2:
        await message.answer("⚠️ Необходимо минимум 2 варианта ответа. Попробуйте снова:")
        return

    if len(options) > 10:
        await message.answer("⚠️ Максимум 10 вариантов ответа. Попробуйте снова:")
        return

    # Get question
    data = await state.get_data()
    question = data['poll_question']

    # Create poll
    poll_id = await db.create_poll(question, options)

    await state.clear()

    # Send poll to all users
    users = await db.get_all_users()

    text = f"📊 **Новый опрос**\n\n{question}"
    keyboard = get_poll_keyboard(poll_id, options)

    await message.answer(f"📤 Отправка опроса {len(users)} участникам...")

    success_count = 0
    failed_count = 0

    for user in users:
        try:
            await bot.send_message(
                chat_id=user['user_id'],
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            success_count += 1
        except Exception:
            failed_count += 1

    result_text = f"""
✅ **Опрос создан и разослан**

Успешно: {success_count}
Ошибок: {failed_count}

Для просмотра результатов используйте кнопку "📊 Результаты" в опросе.
"""
    keyboard_back = get_back_to_admin_keyboard()
    await message.answer(result_text, reply_markup=keyboard_back, parse_mode="Markdown")


@router.callback_query(F.data.startswith("vote_"))
async def vote_in_poll(callback: CallbackQuery, db: Database):
    """Handle poll vote."""
    parts = callback.data.split("_")
    poll_id = int(parts[1])
    option_index = int(parts[2])

    user_id = callback.from_user.id

    # Try to vote
    success = await db.vote_poll(poll_id, user_id, option_index)

    if success:
        poll = await db.get_poll(poll_id)
        if poll and poll['is_active']:
            selected_option = poll['options'][option_index]
            await callback.answer(f"✅ Вы проголосовали за: {selected_option}", show_alert=True)
        else:
            await callback.answer("✅ Голос принят", show_alert=True)
    else:
        await callback.answer("⚠️ Вы уже проголосовали в этом опросе", show_alert=True)


@router.callback_query(F.data.startswith("poll_results_"))
async def show_poll_results(callback: CallbackQuery, db: Database):
    """Show poll results."""
    poll_id = int(callback.data.split("_")[2])

    poll = await db.get_poll(poll_id)
    if not poll:
        await callback.answer("Опрос не найден", show_alert=True)
        return

    results = await db.get_poll_results(poll_id)
    total_votes = sum(results.values())

    text = f"📊 **Результаты опроса**\n\n{poll['question']}\n\n"

    if total_votes == 0:
        text += "Пока никто не проголосовал."
    else:
        for i, option in enumerate(poll['options']):
            votes = results.get(i, 0)
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0

            # Create visual bar
            bar_length = int(percentage / 10)
            bar = "▓" * bar_length + "░" * (10 - bar_length)

            text += f"\n{option}\n"
            text += f"{bar} {percentage:.1f}% ({votes})\n"

        text += f"\n👥 Всего голосов: {total_votes}"

    # Show close poll button for admins
    if is_admin(callback.from_user.id) and poll['is_active']:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔒 Закрыть опрос",
                    callback_data=f"close_poll_{poll_id}"
                )]
            ]
        )
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback.message.answer(text, parse_mode="Markdown")

    await callback.answer()


@router.callback_query(F.data.startswith("close_poll_"))
async def close_poll_handler(callback: CallbackQuery, db: Database):
    """Close a poll (admin only)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return

    poll_id = int(callback.data.split("_")[2])

    await db.close_poll(poll_id)

    await callback.answer("✅ Опрос закрыт", show_alert=True)
    await callback.message.edit_text(
        callback.message.text + "\n\n🔒 **Опрос закрыт**",
        parse_mode="Markdown"
    )
