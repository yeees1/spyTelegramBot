from aiogram import Bot, Router, types
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command

from database import DB

router = Router()

async def check_administartor(bot: Bot, chat_id: int):
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return False
        return member.can_send_messages and member.can_manage_chat and member.can_send_photos
    except TelegramForbiddenError:
        return False
    except Exception as e:
        print(f"[check_administrator] error: {e}")
        return False

@router.message(Command("connect"))
async def connect(message: types.Message, db: DB):
    pass
