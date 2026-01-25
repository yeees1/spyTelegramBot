from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot
from aiogram.types import Message
from typing import Optional
from aiogram.fsm.storage.base import StorageKey, BaseStorage
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext


router = Router()
from utils.mention import mention

class TurnFlow(StatesGroup):
    active = State()


def group_fsm(storage, bot, group_id: int) -> FSMContext:
    key = StorageKey(bot_id=bot.id, chat_id=group_id, user_id=0)
    return FSMContext(storage=storage, key=key)




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

@router.message_reaction()
async def on_reaction(event: types.MessageReactionUpdated, bot: Bot, storage: BaseStorage):
    group_id = event.chat.id

    fsm = group_fsm(storage, bot, group_id)
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