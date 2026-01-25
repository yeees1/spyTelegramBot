from aiogram import Router, types
from aiogram.filters import Command
from config import admin_id
from database import DB

router = Router()

@router.message(Command("session_list"))
async def session_list(message: types.Message, db: DB):
    if message.from_user.id != int(admin_id): return
    dataSession = await db.getAllSession()
    sessionList = "list\n"
    for el in dataSession:
        tempText = ""
        for info in el:
            tempText+=f"| {info} "
        tempText+='\n'
        if len(sessionList) + len(tempText) > 4000:
            await message.reply(sessionList)
            sessionList = ""
        sessionList+=tempText
    await message.reply(sessionList)

@router.message(Command("users_list"))
async def users_list(message: types.Message, db: DB):
    if message.from_user.id != int(admin_id): return
    dataUsers = await db.getAllUsers()
    usersList = "list\n"
    for el in dataUsers:
        tempText = ""
        for info in el:
            tempText+=f"| {info} "
        tempText+='\n'
        if len(usersList) + len(tempText) > 4000:
            await message.reply(usersList)
            usersList = ""
        usersList+=tempText
    await message.reply(usersList)

@router.message(Command("dell_user"))
async def dell_user(message: types.Message, db: DB):
    if message.from_user.id != int(admin_id): return
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    if payload:
        await db.delUserById(payload)
        req = await db.getUserById(payload)
        if not req: await message.reply("Пользователь успешно удален"); return
        await message.reply("Попробуйте еще раз")

@router.message(Command("spy_list"))
async def spy_list(message: types.Message, db: DB):
    if message.from_user.id != int(admin_id): return
    dataUsers = await db.getAllSpies()
    usersList = "list\n"
    for el in dataUsers:
        tempText = ""
        for info in el:
            tempText+=f"| {info} "
        tempText+='\n'
        if len(usersList) + len(tempText) > 4000:
            await message.reply(usersList)
            usersList = ""
        usersList+=tempText
    await message.reply(usersList)

@router.message(Command("dell_spy"))
async def dell_spy(message: types.Message, db: DB):
    if message.from_user.id != int(admin_id): return
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    if payload:
        await db.delSpiesById(payload)
        req = await db.getSpiesById(payload)
        if not req: await message.reply("Пользователь успешно удален"); return
        await message.reply("Попробуйте еще раз")
@router.message(Command("dell_session"))
async def dell_session(message: types.Message, db: DB):
    if message.from_user.id != int(admin_id): return
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    if payload:
        await db.deleteSession(str(payload))
        req = await db.getSession(str(payload))
        if not req: await message.reply("Сессия успешно удалена"); return
        await message.reply("Попробуйте еще раз")

