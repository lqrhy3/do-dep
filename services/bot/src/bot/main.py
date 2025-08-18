import asyncio
from aiogram import Bot, Dispatcher

from app.settings import settings
from bot.handlers import router


async def main():
    bot = Bot(settings.app.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    allowed = dp.resolve_used_update_types()
    await dp.start_polling(bot, allowed_updates=allowed)


if __name__ == '__main__':
    asyncio.run(main())
