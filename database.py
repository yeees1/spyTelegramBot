import sqlite3

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

async def createTables():
    req = """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER UNIQUE NOT NULL,
            group_name TEXT,
            creator_id INTEGER NOT NULL
        )
        """
    cursor.execute(req)
    req = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            username TEXT,
            telegram_name TEXT,
            session_id INTEGER NOT NULL
        )
        """
    cursor.execute(req)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            image_url TEXT,
            description TEXT
        );
        """)
    conn.commit()

def getSession(condition):
    cursor.execute("SELECT * FROM sessions WHERE group_id=?", (condition, ))
    result = cursor.fetchall()
    if not result: return False
    return result
def insertSession(groupId, groupName, creatorId, spyCount):
    cursor.execute("INSERT INTO sessions (group_id, group_name, creator_id, votestart, spy_count) VALUES (?, ?, ?, 0, ?)", (groupId, groupName, creatorId, spyCount))
    conn.commit()
def getUsersFromSession(condition):
    cursor.execute("SELECT * FROM users WHERE session_id=?", (condition,))
    result = cursor.fetchall()
    if not result: return False
    return result
def getUserInfoFromSession(condition, groupId):
    cursor.execute("SELECT * FROM users WHERE chat_id=? and session_id=?", (condition,groupId))
    result = cursor.fetchall()
    if not result: return False
    return result
def insertUserInSession(chatId, username, telegramName, sessionId):
    cursor.execute("INSERT INTO users (chat_id, username, telegram_name, session_id) VALUES (?, ?, ?, ?)", (chatId, username, telegramName, sessionId))
    conn.commit()
def checkUserInSession(chatId, sessionId):
    cursor.execute("SELECT * FROM users WHERE session_id=? AND chat_id=?", (sessionId, chatId))
    result = cursor.fetchall()
    if not result: return False
    return True
def getInfoFiles():
    cursor.execute("SELECT * FROM files")
    return cursor.fetchall()
def deleteSession(sessionId):
    cursor.execute("DELETE FROM sessions WHERE group_id = ?",(sessionId,))
    cursor.execute("DELETE FROM users WHERE session_id = ?",(sessionId,))
    cursor.execute("DELETE FROM spies WHERE group_id = ?", (sessionId,))
    conn.commit()
def getVotesInSession(groupId):
    cursor.execute("SELECT votes FROM users WHERE session_id = ?", (groupId,))
    result = cursor.fetchall()
    sumVotes = 0
    for el in result: sumVotes+=el[0]
    return result, sumVotes
def updateVotesInSession(groupId, addUserId, voteUserId):
    cursor.execute(
        "UPDATE users SET votes = votes + 1 WHERE chat_id = ? and session_id = ?",
        (addUserId, groupId)
    )
    conn.commit()
    cursor.execute(
        "UPDATE users SET isvote = 1 WHERE chat_id = ? and session_id = ?",
        (voteUserId, groupId)
    )
    conn.commit()
def updateSessionInfo(groupId, cardId, startflag):
    # cursor.execute(
    #     "UPDATE sessions SET spy_id = ? WHERE group_id = ?",
    #     (spyId, groupId)
    # )
    # conn.commit()
    # cursor.execute(
    #     "UPDATE sessions SET card_id = ? WHERE group_id = ?",
    #     (cardId, groupId)
    # )
    # conn.commit()
    cursor.execute("""UPDATE sessions SET card_id = ?, isstart = ? WHERE group_id = ?""", (cardId, startflag, groupId))
    conn.commit()
def updateVoteStatus(groupId, voteFlag):
    cursor.execute("""UPDATE sessions SET votestart = ? WHERE group_id = ?""",
                   (voteFlag, groupId))
    conn.commit()
def getPhoto(photoId):
    cursor.execute("SELECT * FROM files WHERE card_id=?", ( photoId, ))
    result = cursor.fetchone()
    return result
def insertSpiesInfo(chatId, username, groupId):
    cursor.execute("INSERT INTO spies (chat_id, username, group_id) VALUES (?, ?, ?)",
                   (chatId, username, groupId))
    conn.commit()
def getSpies(groupId):
    cursor.execute("SELECT * FROM spies WHERE group_id=?", (groupId,))
    result = cursor.fetchall()
    return result


