
from aiogram.filters import Command
import aiohttp
from aiogram import F, types, Router

from config import admin_id
from database import DB
from services.work_with_api import fetch_official_cards, fetch_descriptions, fetch_json
from services.translate import translate_ru

router = Router()

@router.message(Command("sync_cards"))
async def sync_cards(message: types.Message, db: DB):
    if message.from_user.id != int(admin_id): return
    status_msg = await message.answer("🔄 Загружаю карты Clash Royale...")

    try:
        async with aiohttp.ClientSession() as session:
            cards = await fetch_official_cards(session)
            #print(cards)
            descriptions = await fetch_descriptions(session)

        existing_ids = await db.get_existing_card_ids()
        new_cards = [c for c in cards if c.get("id") not in existing_ids]

        await status_msg.edit_text(
            f"✅ Получено карт: {len(cards)}\n"
            f"🆕 Новых карт для добавления: {len(new_cards)}\n"
            f"🌍 Перевожу описания..."
        )

        added = 0
        total = len(new_cards)
        cardslist = []
        for i, card in enumerate(new_cards, start=1):
            card_id = int(card["id"])
            name = card.get("name", "")
            elexir = card.get("elixirCost")
            rarity = card.get("rarity")
            evo = card.get("maxEvolutionLevel")
            if not evo:
                evo = "нет"
            else:
                evo = "есть"
            icon_urls = card.get("iconUrls") or {}
            image_url = icon_urls.get("medium") or icon_urls.get("small")

            raw_desc = descriptions.get(card_id, "")
            desc_ru = await translate_ru(raw_desc)

            cardslist.append(["""
                INSERT IGNORE INTO files (card_id, name, image_url, description, elixirCost, rarity, is_evo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (card_id, name, image_url, desc_ru, elexir, rarity, evo)])

        added = await db.insert_new_cards(cardslist, total, status_msg)
        await status_msg.edit_text(
            f"✅ Готово!\n"
            f"Всего карт из API: {len(cards)}\n"
            f"Новых обработано: {total}\n"
            f"Добавлено в files: {added}\n"
            f"(существующие записи не изменялись)"
        )

    except aiohttp.ClientResponseError as e:
        await status_msg.edit_text(f"❌ Ошибка API: {e.status}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")
