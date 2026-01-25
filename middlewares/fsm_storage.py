from aiogram import BaseMiddleware
from typing import Any, Dict, Callable, Awaitable

class FSMStorageMiddleware(BaseMiddleware):
    def __init__(self, storage):
        self.storage = storage

    async def __call__(self, handler: Callable, event: Any, data: Dict[str, Any]):
        data["storage"] = self.storage
        return  await handler(event, data)