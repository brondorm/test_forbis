"""Configuration module for the conference bot."""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# Admin configuration
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Stream URL
STREAM_URL = os.getenv('STREAM_URL', 'https://youtube.com/live/stream')

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_database.db')

# Booking limits
MAX_BOOKING_CAPACITY = 50

# Event data (can be moved to database later)
EVENT_PROGRAM = """
📋 **Программа конференции**

**09:00 - 10:00** - Регистрация участников
**10:00 - 11:00** - Открытие конференции
**11:00 - 13:00** - Доклады секции A
**13:00 - 14:00** - Обед
**14:00 - 16:00** - Доклады секции B
**16:00 - 16:30** - Кофе-брейк
**16:30 - 18:00** - Панельная дискуссия
**18:00 - 18:30** - Закрытие
"""

EVENT_SCHEDULE = """
🗓 **Расписание**

**День 1 (15 ноября)**
• 10:00 - Открытие
• 11:00 - Воркшоп по AI
• 14:00 - Нетворкинг

**День 2 (16 ноября)**
• 10:00 - Мастер-классы
• 14:00 - Круглый стол
• 17:00 - Закрытие
"""

SPEAKERS = [
    {
        'id': 1,
        'name': 'Иван Иванов',
        'title': 'CTO, Tech Company',
        'bio': 'Эксперт в области машинного обучения с 10-летним опытом',
        'photo': None  # Can add photo file_id here
    },
    {
        'id': 2,
        'name': 'Мария Петрова',
        'title': 'Head of AI Research',
        'bio': 'Специалист по нейронным сетям и компьютерному зрению',
        'photo': None
    },
    {
        'id': 3,
        'name': 'Алексей Сидоров',
        'title': 'Senior Developer',
        'bio': 'Full-stack разработчик, спикер международных конференций',
        'photo': None
    }
]

# Map image file_id (upload once and save the file_id)
MAP_IMAGE_PATH = 'assets/conference_map.jpg'  # Local path or file_id
