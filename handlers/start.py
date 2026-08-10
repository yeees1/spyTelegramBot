from aiogram import Bot, Router, types
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.utils.chat_member import MEMBERS

from database import DB

router = Router()

async def is_group_member(bot: Bot, group_id: int | str, user_id: int | str) -> bool:
    try:
        member = await bot.get_chat_member(group_id, user_id)
    except (TelegramBadRequest, TelegramForbiddenError):
        return False
    return isinstance(member, MEMBERS)

@router.message(CommandStart())
async def start_handler(message: types.Message, db:DB, bot: Bot):
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    usernaaame = message.from_user.username
    if not usernaaame:
        usernaaame = "нет юзернейма"
    await db.insertNewUser(str(message.from_user.id), usernaaame)
    if payload:
        req = await db.getSession(payload)
        if req == False: await message.answer("❌ Такой игры не существует"); return
        userId = str(message.from_user.id)
        if not await is_group_member(bot, payload, userId):
            await message.answer("❌ Участвовать в игре могут только участники группы")
            return
        usersCount = len(await db.getUsersFromSession(payload))
        if usersCount+1 > 30: await message.answer("❌ Достигнут лимит в 30 игроков"); return
        if req[0][6] == 1: await message.answer("❌ Игра уже запущена"); return
        checkUser = await db.checkUserInSession(userId, payload)
        if not checkUser:
            username = message.from_user.username
            if not username: username = "юзернейма нет"
            await db.insertUserInSession(userId, username, message.from_user.full_name, payload)
            await message.answer("✅ Вы принимаете участие в игре")
            return
        await message.answer("❌ Вы уже участвуете")
        return
    await message.answer("❌ Бот используется только в группе")
