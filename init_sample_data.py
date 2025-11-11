"""Script to initialize sample activities in the database."""
import asyncio
from bot.database import Database
from bot.config import DATABASE_PATH


async def init_sample_activities():
    """Initialize sample activities."""
    db = Database(DATABASE_PATH)
    await db.init_db()

    # Sample activities
    activities = [
        {
            'name': 'Воркшоп по AI и ML',
            'description': 'Практический воркшоп по применению машинного обучения в реальных проектах',
            'date_time': '15 ноября, 11:00',
            'max_capacity': 50
        },
        {
            'name': 'Нетворкинг-сессия',
            'description': 'Неформальное общение участников, обмен контактами и опытом',
            'date_time': '15 ноября, 14:00',
            'max_capacity': 50
        },
        {
            'name': 'Мастер-класс по Python',
            'description': 'Продвинутые техники программирования на Python для профессионалов',
            'date_time': '16 ноября, 10:00',
            'max_capacity': 30
        },
        {
            'name': 'Круглый стол: Будущее IT',
            'description': 'Дискуссия о трендах и перспективах развития IT-индустрии',
            'date_time': '16 ноября, 14:00',
            'max_capacity': 50
        }
    ]

    for activity in activities:
        activity_id = await db.add_activity(**activity)
        print(f"✅ Создана активность: {activity['name']} (ID: {activity_id})")

    print("\n✅ Инициализация завершена!")
    print(f"Создано активностей: {len(activities)}")


if __name__ == '__main__':
    asyncio.run(init_sample_activities())
