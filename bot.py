import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import router
from database import init_db, seed_gifts


async def main():
    bot = Bot(token=BOT_TOKEN)

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    await init_db()
    await seed_gifts()

    print("Bot ishga tushdi...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
