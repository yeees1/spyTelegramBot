import aiohttp
from typing import Optional, Dict

from config import CR_API_TOKEN, OFFICIAL_CARDS_URL, DESCRIPTIONS_URL

async def fetch_json(session: aiohttp.ClientSession, url: str, headers: Optional[dict] = None):
    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        resp.raise_for_status()
        return await resp.json()


async def fetch_official_cards(session: aiohttp.ClientSession):
    headers = {
        "Authorization": f"Bearer {CR_API_TOKEN}",
        "Accept": "application/json",
    }
    data = await fetch_json(session, OFFICIAL_CARDS_URL, headers)
    return data.get("items", [])


async def fetch_descriptions(session: aiohttp.ClientSession) -> Dict[int, str]:
    items = await fetch_json(session, DESCRIPTIONS_URL)
    return {
        int(card["id"]): card.get("description", "").strip()
        for card in items
        if "id" in card
    }