import asyncio
from googletrans import Translator

translator = Translator()

async def translate_ru(text: str) -> str:
    if not text:
        return ""
    try:
        # googletrans синхронный → в отдельный поток + таймаут
        res = await asyncio.wait_for(
            asyncio.to_thread(translator.translate, text, src="en", dest="ru"),
            timeout=8
        )
        return res.text
    except Exception:
        # если перевод отвалился/завис — оставляем английский
        return text

def translate_description(text: str) -> str:
    if not text:
        return ""

    try:
        result = translator.translate(text, src="en", dest="ru")
        return result.text
    except Exception:
        return text