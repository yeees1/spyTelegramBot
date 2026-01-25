from aiogram import Bot, Router, types
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command

from database import DB

router = Router()

async def check_permissions(bot: Bot, chat_id: int):
    try:
        can_send_messages = True
        can_send_photos = True
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return [False, {}]
        try:
            await bot.send_message(chat_id, "TEST")
        except:
            can_send_messages = False
        try:
            await bot.send_photo(chat_id, "https://investvolga.volgograd.ru/upload/iblock/7b9/Test_Logo_Circle_black_transparent.png")
        except:
            can_send_photos = False
        return [can_send_messages and member.can_manage_chat and can_send_photos, {"Отправка сообщений": can_send_messages,"manage_chat": member.can_manage_chat,"Отправка фото": can_send_photos}]
    except TelegramForbiddenError:
        return [False, {}]
    except Exception as e:
        print(f"[check_permissions] error: {e}")
        return [False, {}]

async def check_administrator(bot: Bot, chat_id: int):
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return False
        return True
    except Exception as e:
        print(f"[check_administrator] error: {e}")
        return False

@router.message(Command("connect"))
async def connect(message: types.Message, db: DB, bot: Bot):
    data = await db.getGroupInfo(message.chat.id)
    permissionData = await check_permissions(bot, message.chat.id)
    administratorFlag = await check_administrator(bot, message.chat.id)
    if data != False and permissionData[0] == True and administratorFlag == True: await message.answer("✅ Группа уже привязана, бот - администратор с нужными правами"); return
    if data != False:
        await db.deleteGroup(message.chat.id)
        answerText = "Отключенные парва:\n"
        for el in permissionData[1].keys():
            if permissionData[1][el] == False:
                answerText += f"{el}\n"

        answerText += f"Наличие роил администратора {administratorFlag}\n❌ Привязка группы удалена до восстановления прав.\nПосле выполения условий воспользуйтесь командой /connect или запустите игру"
        await message.answer(answerText)
        return
    if data == False:
        if permissionData[0] == True and administratorFlag == True:
            await db.insertGroup(message.chat.id)
            await message.answer("✅ Группа привязана")
            return
        answerText = f"❌ Группа не привязана!\nНаличие роил администратора {administratorFlag}\nОтключенные парва:\n"
        for el in permissionData[1].keys():
            if permissionData[1][el] == False:
                answerText += f"{el}\n"
        answerText += "После выполения условий воспользуйтесь командой /connect или запустите игру"




