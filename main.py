"""Main entry point for the conference Telegram bot."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, DATABASE_PATH
from bot.database import Database
from bot.handlers import user, booking, admin, polls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Initialize database
    db = Database(DATABASE_PATH)
    await db.init_db()
    logger.info("Database initialized")

    # Register routers
    dp.include_router(user.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)
    dp.include_router(polls.router)

    # Make database available to all handlers
    dp['db'] = db

    # Middleware to pass database to handlers
    @dp.update.middleware()
    async def db_middleware(handler, event, data):
        data['db'] = db
        return await handler(event, data)

    # Middleware to log callback queries
    @dp.callback_query.middleware()
    async def log_callback_middleware(handler, event, data):
        logger.info(f"Callback query received: data='{event.data}' from user={event.from_user.id}")
        result = await handler(event, data)
        logger.info(f"Callback query handled: data='{event.data}'")
        return result

    logger.info("Bot starting...")

    try:
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
