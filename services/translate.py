import asyncio
from googletrans import Translator

translator = Translator()

async def translate_ru(text: str) -> str:
    if not text:
        return ""
    try:
        # googletrans синхронный -> в отдельный поток + таймаут
        return await asyncio.wait_for(
            asyncio.to_thread(
                lambda: translator.translate(text, dest="ru").text
            ),
            timeout=8
        )
    except Exception as e:
        print(f"[translate] failed: {e}")
        return text
