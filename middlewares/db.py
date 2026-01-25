from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

class DbMiddleware(BaseMiddleware):
    def __init__(self, db):
        self.db = db

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        data["db"] = self.db
        return  await handler(event, data)