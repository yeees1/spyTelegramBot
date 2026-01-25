from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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