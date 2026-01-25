import aiomysql
from typing import Any, Optional
# ===================== class DB =====================
class DB:
    def __init__(self, host: str, port: int, user: str, password: str, db: str):
        self._cfg = dict(host=host, port=port, user=user, password=password, db=db)
        self.pool: Optional[aiomysql.Pool] = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(
            minsize=1,
            maxsize=10,
            autocommit=False,
            **self._cfg,
        )

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def execute(self, query: str, params: tuple = ()) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()
                return cur.rowcount

    async def fetchone(self, query: str, params: tuple = ()) -> Any:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetchall(self, query: str, params: tuple = ()) -> list[Any]:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchall()
# ===================== create all tables in db =====================
    async def createTables(self):
        await self.execute("""CREATE TABLE IF NOT EXISTS sessions (
                  id BIGINT AUTO_INCREMENT PRIMARY KEY,
                  group_id BIGINT NOT NULL UNIQUE,
                  group_name TEXT,
                  creator_id BIGINT NOT NULL,
                  card_id BIGINT DEFAULT 0,
                  votestart TEXT,
                  isstart INT DEFAULT 0,
                  spy_count INT
                );""")

        await self.execute("""CREATE TABLE IF NOT EXISTS users (
                  id BIGINT AUTO_INCREMENT PRIMARY KEY,
                  chat_id BIGINT NOT NULL,
                  username TEXT,
                  telegram_name TEXT,
                  session_id BIGINT NOT NULL,
                  votes INT NOT NULL DEFAULT 0,
                  isvote INT NOT NULL DEFAULT 0
                );""")

        await self.execute("""CREATE TABLE IF NOT EXISTS files (
                  id BIGINT AUTO_INCREMENT PRIMARY KEY,
                  card_id BIGINT NOT NULL UNIQUE,
                  name TEXT NOT NULL,
                  image_url TEXT,
                  description TEXT,
                  elixirCost INT,
                  rarity TEXT,
                  is_evo TEXT
                );""")

        await self.execute("""CREATE TABLE IF NOT EXISTS allusers (
                  id BIGINT AUTO_INCREMENT PRIMARY KEY,
                  chat_id TEXT,
                  username TEXT
                );""")

        await self.execute("""CREATE TABLE IF NOT EXISTS spies (
                  id BIGINT AUTO_INCREMENT PRIMARY KEY,
                  chat_id TEXT,
                  username TEXT,
                  group_id TEXT
                );""")

        await self.execute("""CREATE TABLE IF NOT EXISTS `groups` (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL UNIQUE
        );""")

# ===================== main function with db =====================
    async def getSession(self, group_id):
        rows = await self.fetchall(
            "SELECT * FROM sessions WHERE group_id=%s",
            (group_id, )
        )
        return rows if rows else False

    async def insertSession(self, groupId, groupName, creatorId, spyCount):
        await self.execute(
            "INSERT INTO sessions (group_id, group_name, creator_id, votestart, spy_count) VALUES (%s, %s, %s, 0, %s)",
            (groupId, groupName, creatorId, spyCount)
        )

    async def getUsersFromSession(self, session_id):
        rows = await self.fetchall(
            "SELECT * FROM users WHERE session_id=%s",
            (session_id,)
        )
        return rows if rows else False

    async def getUserInfoFromSession(self, chat_id, group_id):
        rows = await self.fetchall(
            "SELECT * FROM users WHERE chat_id=%s and session_id=%s",
            (chat_id, group_id)
        )
        return rows if rows else False

    async def insertUserInSession(self, chat_id, username, telegram_name, session_id):
        await self.execute(
            "INSERT INTO users (chat_id, username, telegram_name, session_id) VALUES (%s, %s, %s, %s)",
            (chat_id, username, telegram_name, session_id)
        )

    async def checkUserInSession(self, chat_id, session_id):
        rows = await self.fetchall(
            "SELECT * FROM users WHERE session_id=%s AND chat_id=%s",
            (session_id, chat_id)
        )
        return rows if rows else False

    async def getInfoFiles(self):
        return await self.fetchall("SELECT * FROM files")

    async def deleteSession(self, session_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM sessions WHERE group_id = %s",
                    (session_id,)
                )
                await cur.execute(
                    "DELETE FROM users WHERE session_id = %s",
                    (session_id,)
                )
                await cur.execute("DELETE FROM spies WHERE group_id = %s",
                                  (session_id,)
                )
            await conn.commit()

    async def getVotesInSession(self, group_id):
        rows = await self.fetchall(
            "SELECT votes FROM users WHERE session_id = %s",
            (group_id,)
        )
        sumVotes = sum(el[0] for el in rows) if rows else 0
        return rows, sumVotes

    async def updateVotesInSession(self, group_id, add_user_id, vote_user_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET votes = votes + 1 WHERE chat_id = %s and session_id = %s",
                    (add_user_id, group_id)
                )
                await cur.execute(
                    "UPDATE users SET isvote = 1 WHERE chat_id = %s and session_id = %s",
                    (vote_user_id, group_id)
                )
            await conn.commit()

    async def updateSessionInfo(self, group_id, card_id, startflag):
        await self.execute(
            "UPDATE sessions SET card_id = %s, isstart = %s WHERE group_id = %s",
            (card_id, startflag, group_id)
        )

    async def updateVoteStatus(self, group_id, voteflag):
        await self.execute(
            "UPDATE sessions SET votestart = %s WHERE group_id = %s",
            (voteflag, group_id)
        )

    async def getPhoto(self, photo_id):
        return await self.fetchone(
            "SELECT * FROM files WHERE card_id=%s",
            (photo_id, )
        )

    async def insertSpiesInfo(self, chat_id, username, group_id):
        await self.execute(
            "INSERT INTO spies (chat_id, username, group_id) VALUES (%s, %s, %s)",
            (chat_id, username, group_id)
        )

    async def getSpies(self, group_id):
        return await self.fetchall(
            "SELECT * FROM spies WHERE group_id=%s",
            (group_id, )
        )

    async def getAllSession(self):
        return await self.fetchall("SELECT * FROM sessions")

    async def getAllUsers(self):
        return await self.fetchall("SELECT * FROM users")

    async def delUserById(self, id):
        await self.execute(
            "DELETE FROM users WHERE id = %s",
            (id, )
        )

    async def getUserById(self, id):
        return await self.fetchall(
            "SELECT * FROM users WHERE id =%s",
            (id, )
        )

    async def getAllSpies(self):
        return await self.fetchall("SELECT * FROM spies")

    async def delSpiesById(self, id):
        await self.execute(
            "DELETE FROM spies WHERE id = %s",
            (id, )
        )

    async def getSpiesById(self, id):
        return await self.fetchall(
            "SELECT * FROM spies WHERE id = %s",
            (id, )
        )
    async def insertNewUser(self, chat_id, username):
        await self.execute(
            "INSERT IGNORE INTO allusers (chat_id, username) VALUES (%s, %s)",
            (chat_id, username)
        )

    async def get_existing_card_ids(self) -> set[int]:
        card_ids = await self.fetchall("SELECT card_id FROM files")
        return {row[0] for row in card_ids}

    async def insert_new_cards(self, cardslist, total, status_msg):
        added = 0
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                for i in range(len(cardslist)):
                    rowcount = await cur.execute(cardslist[i][0], cardslist[i][1])
                    if rowcount == 1:
                        added += 1
                    if i % 10 == 0 or i == total:
                        await status_msg.edit_text(
                            f"🆕 Добавляю новые карты: {i}/{total}\n"
                            f"✅ Уже добавлено: {added}"
                        )
            await conn.commit()
        return added

    async def getGroupInfo(self, group_id):
        row = await self.fetchone(
            "SELECT * FROM `groups` WHERE group_id = %s",
            (group_id, )
        )
        return row if row else False

    async def deleteGroup(self, group_id):
        await self.execute(
            "DELETE FROM `groups` WHERE group_id = %s",
            (group_id,)
        )

    async def insertGroup(self, group_id):
        await self.execute(
            "INSERT INTO `groups`(group_id) VALUES (%s)",
            (group_id,)
        )