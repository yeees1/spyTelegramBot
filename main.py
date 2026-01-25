import asyncio


from aiogram import Bot, Dispatcher
from aiogram.filters import Command

from typing import Dict, Any, Optional
import aiohttp

from aiogram import F, types
from aiogram.fsm.storage.memory import MemoryStorage

from database import DB
from config import TOKEN, CR_API_TOKEN, CR_BASE_URL, OFFICIAL_CARDS_URL, DESCRIPTIONS_URL, admin_id, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD
from middlewares.db import DbMiddleware
from middlewares.fsm_storage import FSMStorageMiddleware
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.game import router as game_router
from handlers.sync_cards import router as sync_router
from services.turn_flow import router as turn_flow_router








# def get_existing_card_ids() -> set[int]:
#     cursor.execute("SELECT card_id FROM files")
#     return {row[0] for row in cursor.fetchall()}
















#работа с апи by gpt



#
# def insert_cards_ignore(cards, descriptions) -> int:
#     added = 0
#
#     for card in cards:
#         card_id = card.get("id")
#         name = card.get("name")
#         elexir = card.get("elixirCost")
#         rarity = card.get("rarity")
#         evo = card.get("maxEvolutionLevel")
#         if not evo: evo = "нет"
#         else: evo = "есть"
#         icon_urls = card.get("iconUrls") or {}
#
#         image_url = icon_urls.get("medium") or icon_urls.get("small")
#         raw_description = descriptions.get(int(card_id), "")
#         description = translate_description(raw_description)
#
#         if not card_id or not name:
#             continue
#
#         cursor.execute(
#             """
#             INSERT OR IGNORE INTO files (card_id, name, image_url, description, elixirCost, rarity, is_evo)
#             VALUES (?, ?, ?, ?, ?, ?, ?)
#             """,
#             (card_id, name, image_url, description, elexir, rarity, evo)
#         )
#
#         if cursor.rowcount == 1:
#             added += 1
#
#     conn.commit()
#     return added









async def main():
    bot = Bot(token=TOKEN, parse_mode="HTML")
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

