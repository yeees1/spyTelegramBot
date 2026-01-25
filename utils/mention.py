from typing import Optional

def mention(user_id: int, username: Optional[str]) -> str:
    if username and username!="юзернейма нет":
        return f"@{username.lstrip('@')}"
    return f'<a href="tg://user?id={user_id}">пользователь</a>'


def extract_turn_user(row) -> tuple[int, Optional[str]]:
    # row = (db_id, telegram_id, username, telegram_name, group_id)
    return int(row[1]), (row[2] if row[2] else None)