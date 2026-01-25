from aiogram import Router, types
from aiogram.filters import CommandStart

from database import DB

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message, db:DB):
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    usernaaame = message.from_user.username
    if not usernaaame:
        usernaaame = "нет юзернейма"
    await db.insertNewUser(str(message.from_user.id), usernaaame)
    if payload:
        req = await db.getSession(payload)
        if req == False: await message.answer("❌ Такой игры не существует"); return
        usersCount = len(await db.getUsersFromSession(payload))
        if usersCount+1 > 30: await message.answer("❌ Достигнут лимит в 30 игроков"); return
        if req[0][6] == 1: await message.answer("❌ Игра уже запущена"); return
        userId = str(message.from_user.id)
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
