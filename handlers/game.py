from aiogram import Router, types, F, Bot
from aiogram.filters import Command
import random
from aiogram.enums import ChatType
from aiogram.fsm.storage.base import StorageKey, BaseStorage

from services.random_generate import generateSpyCount
from database import DB
from utils.mention import mention, extract_turn_user
from keyboards.game import inviteKeyboard, voteKeyboard, creatorKeyboard, cancelKeyboard
from services.turn_flow import group_fsm, send_turn_prompt, TurnFlow
from handlers.connect import check_permissions, check_administrator

router = Router()

@router.message(Command("create"))
async def create_command(message: types.Message, bot: Bot, db: DB):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Бот используется только в группе")
        return
    dataGroup = await db.getGroupInfo(message.chat.id)
    permissionData = await check_permissions(bot, message.chat.id)
    administratorFlag = await check_administrator(bot, message.chat.id)
    if (dataGroup != False and permissionData[0]!=True) or (dataGroup != False and administratorFlag!=True):
        await db.deleteGroup(message.chat.id)
        answerText = "Отключенные парва:\n"
        for el in permissionData[1].keys():
            if permissionData[1][el] == False:
                answerText += f"{el}\n"
        answerText += f"Наличие роли администратора {administratorFlag}\n❌ Привязка группы удалена до восстановления прав.\nПосле выполения условий воспользуйтесь командой /connect или запустите игру"
        await message.answer(answerText)
        return
    if dataGroup == False:
        if permissionData[0] == True and administratorFlag == True:
            await db.insertGroup(message.chat.id)
            await message.answer("✅ Группа привязана")
        else:
            answerText = f"❌ Группа не привязана!\nНаличие роли администратора {administratorFlag}\nОтключенные парва:\n"
            for el in permissionData[1].keys():
                if permissionData[1][el] == False:
                    answerText += f"{el}\n"
            answerText += "После выполения условий воспользуйтесь командой /connect или запустите игру"
            await message.answer(answerText)
            return
    try: await bot.send_message(message.from_user.id, "Создание игры...")
    except: await message.answer("У создателя должен быть запущен бот"); return
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    if payload:
        try:
            spyCount = int(payload)
        except:
            await message.answer(
                "❌ Отправьте команду в формате \n/create {кол-во шпионов n>-2 (если рандомное кол-во, к команде ничего не дописывайте)} \nпример <pre>/create 5</pre>\nЕсли кол-во шпионов будет превышать кол-во игроков, оно выберется рандомно", parse_mode="HTML"); return
        if spyCount < 1: await message.answer(
            "❌ Отправьте команду в формате \n/create {кол-во шпионов n>0 (если рандомное кол-во -1)} \nпример <pre>/create 5</pre>\nЕсли кол-во шпионов будет превышать кол-во игроков, оно выберется рандомно", parse_mode="HTML"); return
    else:
        spyCount = -1
    username = message.from_user.username
    groupId = str(message.chat.id)
    groupName = str(message.chat.full_name)
    creatorId = str(message.from_user.id)
    req = await db.getSession(groupId)
    if req != False: await message.answer("❌ В группе уже создана игра"); return
    await message.answer(f"Пользователь {message.from_user.full_name} создал игру\n", reply_markup= inviteKeyboard(groupId), parse_mode="HTML")
    await db.insertSession(groupId, groupName, creatorId, spyCount)
    await db.insertUserInSession(creatorId, username, message.from_user.full_name, groupId)
    listUsers = f"1. {message.from_user.full_name} | {mention(int(creatorId), message.from_user.username)} | {creatorId}"

    await bot.send_message(
        chat_id = creatorId,
        text = f"Вы создали игру в группе {message.chat.full_name}\nВы уже являетесь участником\nСписок участников:\n"+listUsers,
        #reply_markup=creatorKeyboard(groupId)
        parse_mode="HTML"
    )
    await message.answer(
        text=f"Создана игра\nСписок участников:\n" + listUsers,
        reply_markup=creatorKeyboard(groupId, creatorId),
        parse_mode="HTML"
    )

@router.message(Command("vote"))
async def vote_command(message: types.Message, db: DB):
    groupId = message.chat.id
    req = await db.getSession(groupId)
    isUserInSession = await db.getUserInfoFromSession(message.from_user.id, groupId)
    if not isUserInSession: return
    if req == False: await message.answer("❌ Игры не существует"); return
    if req[0][5] == '1': await message.answer("❌ Голосование уже создано"); return
    dataUsers = await db.getUsersFromSession(groupId)
    votes, sumVotes = await db.getVotesInSession(groupId)
    await db.updateVoteStatus(str(groupId), "1")

    await message.answer("Голосование:", reply_markup=voteKeyboard(dataUsers, votes, groupId))


@router.callback_query(F.data.startswith("addvote"))
async def advote_callback(callback: types.CallbackQuery, db: DB, bot: Bot, storage: BaseStorage):
    data = callback.data.split("_")
    userIndex = data[1]
    groupId = data[2]
    req = await db.getSession(groupId)
    if req == False: await callback.answer("❌ Игры не существует"); return
    voteUser = await db.getUserInfoFromSession(callback.from_user.id, groupId)
    if not voteUser: await callback.answer("❌ Вы не участвуете в игре"); return

    if voteUser[0][6] == 1: await callback.answer("❌ Вы уже голосвали"); return

    dataUsers = await db.getUsersFromSession(groupId)
    await db.updateVotesInSession(groupId, dataUsers[int(userIndex)][1], callback.from_user.id)
    votes, sumVotes = await db.getVotesInSession(groupId)

    if sumVotes < len(dataUsers):
        await callback.message.edit_reply_markup(
            reply_markup=voteKeyboard(dataUsers, votes, groupId)
        )
    else:
        dataUsers = await db.getUsersFromSession(groupId)
        listVotes = ""
        for el in dataUsers:
            username = el[2]
            if not username: username = el[3]
            listVotes+=f"@{username} - {el[5]}\n"
        # spy_data = getUserInfo(req[0][5])
        # spy_username = spy_data[0][2]
        # if not spy_username: spy_username = spy_data[0][3]
        spyList = ""
        dataSpies = await db.getSpies(groupId)
        for el in dataSpies:
            spyList += f"{mention(int(el[1]), el[2])}\n"
        await callback.message.edit_text("Голосование окончено\n" + listVotes + f"Шпионы:\n"+spyList)
        cardData = await db.getPhoto(req[0][4])
        await bot.send_photo(chat_id=groupId, photo=cardData[3], caption="Загаданная карта - " + cardData[2])
        await db.deleteSession(groupId)
        fsm = group_fsm(storage, bot, int(groupId))
        await fsm.clear()
        await bot.send_message(
            chat_id=groupId,
            text="🛑 Игра окончена"
        )

    await callback.answer("Голос учтен")

@router.callback_query(F.data.startswith("refresh_list"))
async def refresh_list_callback(callback: types.CallbackQuery, db: DB):
    groupId = callback.data.split("_")[2]
    listUsers = "\n"
    req = await db.getSession(groupId)
    if req == False: await callback.answer("❌ Игры не существует"); return
    dataUsers = await db.getUsersFromSession(groupId)
    oldText = callback.message.text
    for i in range(len(dataUsers)):

        listUsers+=f"{i+1}. {dataUsers[i][3]} | {mention(int(dataUsers[i][1]), dataUsers[i][2])} | {dataUsers[i][1]}\n"
    try:
        await callback.message.edit_text(
            oldText.split("\n")[0]+listUsers,
            reply_markup = creatorKeyboard(groupId, req[0][3]),
            parse_mode="HTML"
        )
        await callback.answer("Обновлено")
    except:
        await callback.answer("Новые игроки пока не добавлялись")

@router.callback_query(F.data.startswith("start_game"))
async def start_game_callback(callback: types.CallbackQuery, db: DB, bot: Bot, storage: BaseStorage):

    calldata = callback.data.split("_")
    groupId = calldata[2]
    creatorId = calldata[3]
    if creatorId != str(callback.from_user.id): await callback.answer("❌ Запустить игру может только создатель", show_alert=True); return
    await callback.message.edit_reply_markup(reply_markup=cancelKeyboard(groupId, "0"))
    req = await db.getSession(groupId)
    if req == False: await callback.answer("❌ Такой игры не существует", show_alert=True); return
    await callback.answer()
    dataUsers = await db.getUsersFromSession(groupId)
    dataCards = await db.getInfoFiles()
    spyCount = req[0][7]
    if spyCount >= len(dataUsers) or spyCount == -1:
        spyCount = generateSpyCount(len(dataUsers))
    lst = [1] * spyCount + [0] * (len(dataUsers) - spyCount)
    random.shuffle(lst)
    cardIndex = random.randint(0, len(dataCards)-1)
    #print(len(dataUsers), len(dataCards), cardIndex, dataUsers)
    await db.updateSessionInfo(groupId, dataCards[cardIndex][1], 1)
    for i in range(len(dataUsers)):
        if lst[i] == 1:
            await db.insertSpiesInfo(dataUsers[i][1], dataUsers[i][2], groupId)
            await bot.send_photo(
                chat_id=dataUsers[i][1],
                photo="https://game.jofo.me/data/userfiles/95/images/2046693-advokat.jpg",
                caption = f"Твоя роль в игре в группе {req[0][2]}<blockquote>шпион</blockquote>",
                parse_mode="HTML"
            )
        else:
            await bot.send_photo(
                chat_id=dataUsers[i][1],
                photo=dataCards[cardIndex][3],
                caption=f"Твоя роль в игре в группе {req[0][2]}:<blockquote>{dataCards[cardIndex][2]}</blockquote>\nРедкость: <blockquote>{dataCards[cardIndex][6]}</blockquote>\nЭлексир: <blockquote>{dataCards[cardIndex][5]}</blockquote>\nЭволюция: <blockquote>{dataCards[cardIndex][7]}</blockquote>\nОписание:<blockquote>{dataCards[cardIndex][4]}</blockquote>",
                parse_mode="HTML",
            )
    #deleteSession(groupId)
    players = [extract_turn_user(r) for r in dataUsers]  # (telegram_id, username)
    random.shuffle(players)

    fsm = group_fsm(storage, bot, int(groupId))
    await fsm.set_state(TurnFlow.active)
    await fsm.set_data({
        "order_ids": [p[0] for p in players],
        "order_names": [p[1] for p in players],
        "idx": 0,
        "prompt_message_id": 0,
        "triggered": False,
    })

    await send_turn_prompt(bot, int(groupId), fsm)






@router.callback_query(F.data.startswith("cancel"))
async def cancel_callback(callback: types.CallbackQuery, db: DB, bot: Bot, storage: BaseStorage):
    await callback.answer()

    calldata = callback.data.split("_")
    groupId = calldata[1]
    voteflag = calldata[2]
    listVotes = ""
    isUserInSession = await db.getUserInfoFromSession(callback.from_user.id, groupId)
    if not isUserInSession: await callback.answer("❌ Вы не являетесь участником игры", show_alert=True); return
    req = await db.getSession(groupId)
    if req == False: print(req, groupId); await callback.message.answer("❌ Такой игры не существует"); return
    if voteflag == "1":
        dataUsers = await db.getUsersFromSession(groupId)
        for el in dataUsers:
            username = el[2]
            if not username: username = el[3]
            listVotes+=f"{mention(int(el[1]), el[2])} - {el[5]}\n"
    # spy_data = getUserInfo(req[0][5])
    # spy_username = spy_data[0][2]
    # if not spy_username: spy_username = spy_data[0][3]
    await callback.message.edit_text("🛑 Игра окончена\n" + listVotes)
    cardData = await db.getPhoto(req[0][4])
    spyList = ""
    dataSpies = await db.getSpies(groupId)
    for el in dataSpies:
        spyList+=f"{mention(int(el[1]), el[2])}\n"
    await bot.send_photo(chat_id=groupId, photo=cardData[3], caption="Загаданная карта - " + cardData[2] + f"\nШпионы:\n" + spyList)
    await db.deleteSession(groupId)
    fsm = group_fsm(storage, bot, int(groupId))
    await fsm.clear()
    # await bot.send_message(
    #     chat_id=groupId,
    #     text="🛑 Игра окончена"
    # )
