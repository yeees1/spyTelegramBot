import asyncio


from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any, Optional
import aiohttp
from googletrans import Translator
from aiogram import F, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
import random
import os
from dotenv import load_dotenv

from database import DB
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CR_API_TOKEN = os.getenv("CR_API_TOKEN")
CR_BASE_URL = "https://proxy.royaleapi.dev"
OFFICIAL_CARDS_URL = f"{CR_BASE_URL}/v1/cards"
DESCRIPTIONS_URL = "https://royaleapi.github.io/cr-api-data/json/cards.json"
DB_PATH = "data.db"
admin_id = os.getenv("ADMIN_ID")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DB = os.getenv("MYSQL_DB", "botdb")
MYSQL_USER = os.getenv("MYSQL_USER", "botuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

translator = Translator()

db = DB(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    db=MYSQL_DB,
)

class TurnFlow(StatesGroup):
    active = State()


def group_fsm(dp, bot, group_id: int) -> FSMContext:
    # общее состояние на всю группу (user_id=0)
    key = StorageKey(bot_id=bot.id, chat_id=group_id, user_id=0)
    return FSMContext(storage=dp.storage, key=key)


def mention(user_id: int, username: Optional[str]) -> str:
    if username and username!="юзернейма нет":
        return f"@{username.lstrip('@')}"
    return f'<a href="tg://user?id={user_id}">пользователь</a>'


def extract_turn_user(row) -> tuple[int, Optional[str]]:
    # row = (db_id, telegram_id, username, telegram_name, group_id)
    return int(row[1]), (row[2] if row[2] else None)


async def send_turn_prompt(bot, group_id: int, fsm: FSMContext):
    data = await fsm.get_data()
    order_ids: list[int] = data["order_ids"]
    order_names: list[Optional[str]] = data["order_names"]
    idx: int = data["idx"]

    uid = order_ids[idx]
    uname = order_names[idx]

    msg = await bot.send_message(
        chat_id=group_id,
        text=(
            f"Отвечает {mention(uid, uname)}\n\n"
            f"👉 Поставьте любую реакцию на это сообщение, чтобы передать ход следующему."
        ),
        parse_mode="HTML",
    )

    await fsm.update_data(prompt_message_id=msg.message_id, triggered=False)

# def get_existing_card_ids() -> set[int]:
#     cursor.execute("SELECT card_id FROM files")
#     return {row[0] for row in cursor.fetchall()}


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

def generateSpyCount(usersCount):
    first_end = int(usersCount * 0.34)
    second_end = int(usersCount * 0.67)
    r = random.random()
    if r < 0.50:
        return random.randint(0, first_end)
    elif r < 0.50 + 0.35:
        return random.randint(first_end + 1, second_end)
    else:
        return random.randint(second_end + 1, usersCount)

def cancelKeyboard(groupId, voteFlag):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Закончить игру", callback_data=f"cancel_{groupId}_{voteFlag}"),
            ]
        ]
    )

def creatorKeyboard(groupId, creatorId):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить список", callback_data=f"refresh_list_{groupId}"),
                InlineKeyboardButton(text="🎮 Начать игру", callback_data=f"start_game_{groupId}_{creatorId}"),
            ]
        ]
    )
def voteKeyboard(dataUsers, votes, groupId):
    keyboard = []
    for i in range(len(dataUsers)):
        username = dataUsers[i][2]
        if not username or username == 'юзернейма нет':
            username = dataUsers[i][3]
        if len(username)>25: username = username[:22]+"..."
        keyboard.append([
            InlineKeyboardButton(
                text=f"@{username} - {votes[i][0]}",
                callback_data=f"addvote_{i}_{groupId}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Закончить голосование",
            callback_data=f"cancel_{groupId}_1"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def inviteKeyboard(groupId):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Участвовать",
                    url=f"https://t.me/spyssss_bot?start={groupId}"
                )
            ]
        ]
    )
@dp.message(CommandStart())
async def start_handler(message: types.Message):
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
        if req[0][6] == "1": await message.answer("❌ Игра уже запущена"); return
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


@dp.message(Command("create"))
async def create_command(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer("❌ Бот используется только в группе")
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

@dp.message(Command("vote"))
async def vote_command(message: types.Message):
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


@dp.callback_query(F.data.startswith("addvote"))
async def advote_callback(callback: types.CallbackQuery):
    data = callback.data.split("_")
    userIndex = data[1]
    groupId = data[2]
    req = await db.getSession(groupId)
    if req == False: await callback.answer("❌ Игры не существует"); return
    voteUser = await db.getUserInfoFromSession(callback.from_user.id, groupId)
    if not voteUser: await callback.answer("❌ Вы не участвуете в игре"); return
    print(voteUser[0][6], type(voteUser[0][6]))
    if voteUser[0][6] == '1': await callback.answer("❌ Вы уже голосвали"); return

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
        fsm = group_fsm(dp, bot, int(groupId))
        await fsm.clear()
        await bot.send_message(
            chat_id=groupId,
            text="🛑 Игра окончена"
        )

    await callback.answer("Голос учтен")

@dp.callback_query(F.data.startswith("refresh_list"))
async def refresh_list_callback(callback: types.CallbackQuery):
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

@dp.callback_query(F.data.startswith("start_game"))
async def start_game_callback(callback: types.CallbackQuery):

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
    await db.updateSessionInfo(groupId, dataCards[cardIndex][1], "1")
    for i in range(len(dataUsers)):
        if lst[i] == 1:
            await db.insertSpiesInfo(dataUsers[i][1], dataUsers[i][2], groupId)
            await bot.send_photo(
                chat_id=dataUsers[i][1],
                photo="https://game.jofo.me/data/userfiles/95/images/2046693-advokat.jpg",
                caption = f"Твоя роль в игре в группе {req[0][2]}<blockquote>шпион</blockquote>"
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

    fsm = group_fsm(dp, bot, int(groupId))
    await fsm.set_state(TurnFlow.active)
    await fsm.set_data({
        "order_ids": [p[0] for p in players],
        "order_names": [p[1] for p in players],
        "idx": 0,
        "prompt_message_id": 0,
        "triggered": False,
    })

    await send_turn_prompt(bot, int(groupId), fsm)

@dp.message(Command("session_list"))
async def session_list(message: types.Message):
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

@dp.message(Command("users_list"))
async def users_list(message: types.Message):
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

@dp.message(Command("dell_user"))
async def session_list(message: types.Message):
    if message.from_user.id != int(admin_id): return
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    if payload:
        await db.delUserById(payload)
        req = await db.getUserById(payload)
        if not req: await message.reply("Пользователь успешно удален"); return
        await message.reply("Попробуйте еще раз")

@dp.message(Command("spy_list"))
async def spy_list(message: types.Message):
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

@dp.message(Command("dell_spy"))
async def spy_list(message: types.Message):
    if message.from_user.id != int(admin_id): return
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    if payload:
        await db.delSpiesById(payload)
        req = await db.getSpiesById(payload)
        if not req: await message.reply("Пользователь успешно удален"); return
        await message.reply("Попробуйте еще раз")
@dp.message(Command("dell_session"))
async def session_list(message: types.Message):
    if message.from_user.id != int(admin_id): return
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) == 2 else None
    if payload:
        await db.deleteSession(str(payload))
        req = await db.getSession(str(payload))
        if not req: await message.reply("Сессия успешно удалена"); return
        await message.reply("Попробуйте еще раз")

@dp.message_reaction()
async def on_reaction(event: types.MessageReactionUpdated):
    group_id = event.chat.id

    fsm = group_fsm(dp, bot, group_id)
    if await fsm.get_state() != TurnFlow.active.state:
        return

    data = await fsm.get_data()

    # проверяем, что реакция именно на текущее сообщение "Отвечает..."
    if event.message_id != data.get("prompt_message_id"):
        return

    # если реакцию убрали — игнор
    if not event.new_reaction:
        return

    # защита от повторных срабатываний на одно и то же сообщение
    if data.get("triggered"):
        return

    order_ids: list[int] = data["order_ids"]
    idx: int = data["idx"]

    idx = (idx + 1) % len(order_ids)

    await fsm.update_data(idx=idx, triggered=True)
    await send_turn_prompt(bot, group_id, fsm)





@dp.callback_query(F.data.startswith("cancel"))
async def cancel_callback(callback: types.CallbackQuery):
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
    fsm = group_fsm(dp, bot, int(groupId))
    await fsm.clear()
    # await bot.send_message(
    #     chat_id=groupId,
    #     text="🛑 Игра окончена"
    # )




#работа с апи by gpt

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



@dp.message(Command("sync_cards"))
async def sync_cards(message: types.Message):
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

        await db.insert_new_cards(cardslist, total, status_msg)
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






async def main():
    await db.connect()
    await db.createTables()
    await dp.start_polling(bot)
    dp["db"] = db
    try:
        await dp.start_polling(bot)
    finally:
        print("shutting down...")
        await db.close()
        print("DB closed")

if __name__ == "__main__":
    asyncio.run(main())

