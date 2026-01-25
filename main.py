import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import DB
from config import TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD
from middlewares.db import DbMiddleware
from middlewares.fsm_storage import FSMStorageMiddleware
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.game import router as game_router
from handlers.sync_cards import router as sync_router
from services.turn_flow import router as turn_flow_router



async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    db = DB(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DB,
    )
    await db.connect()
    await db.createTables()
    dp.update.middleware(DbMiddleware(db))
    dp.update.middleware(FSMStorageMiddleware(dp.storage))
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(game_router)
    dp.include_router(sync_router)
    dp.include_router(turn_flow_router)

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        print("shutting down...")
        await db.close()
        print("DB closed")

if __name__ == "__main__":
    asyncio.run(main())

