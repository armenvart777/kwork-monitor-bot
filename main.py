import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database import db
from handlers import router, _do_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


BOT_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="check", description="Новые заказы на бирже"),
    BotCommand(command="all", description="Все подходящие заказы"),
    BotCommand(command="settings", description="Настройки"),
    BotCommand(command="status", description="Статус мониторинга"),
]


async def scheduler(bot: Bot):
    """Periodically check Kwork exchange for new projects."""
    await asyncio.sleep(30)

    checks_since_heartbeat = 0
    heartbeat_every = 12  # раз в час (12 × 5 мин = 60 мин)

    while True:
        try:
            if await db.is_monitoring_active():
                admin_id = await db.get_admin_id()
                if admin_id:
                    logger.info("Running scheduled check...")
                    await _do_check(bot, admin_id, only_new=True, silent=True)
                    checks_since_heartbeat += 1

                    if checks_since_heartbeat >= heartbeat_every:
                        checks_since_heartbeat = 0
                        seen = await db.get_seen_count()
                        await bot.send_message(
                            admin_id,
                            f"💚 Мониторинг работает\n"
                            f"Проверок за час: {heartbeat_every}\n"
                            f"Всего просмотрено заказов: {seen}",
                        )
        except Exception as e:
            logger.error("Scheduler error: %s", e)

        await asyncio.sleep(settings.check_interval)


async def main():
    if not settings.bot_token:
        logger.error("BOT_TOKEN is not set! Check your .env file.")
        return

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await db.connect()
    logger.info("Database connected")

    # Set bot menu commands (button on the left)
    await bot.set_my_commands(BOT_COMMANDS)
    logger.info("Bot commands menu set")

    asyncio.create_task(scheduler(bot))
    logger.info("Scheduler started (interval: %ds)", settings.check_interval)

    try:
        logger.info("Bot starting...")
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
