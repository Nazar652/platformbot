import asyncio
import logging
import threading

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from config import BOT_TOKEN
from admin_bot import start_bot


router = Router()


class NewBot(StatesGroup):
    writing_bot_token = State()


@router.message(Command(commands=["start"]))
async def command_start(m: Message) -> None:
    await m.answer(f'Привітальне повідомлення\nСтворити бота: /newbot')


@router.message(Command(commands=["newbot"]))
async def command_new_bot(m: Message, state: FSMContext) -> None:
    await m.answer(f'Надішліть бот токен')
    await state.set_state(NewBot.writing_bot_token)


@router.message(NewBot.writing_bot_token)
async def new_bot_token(m: Message) -> None:
    bot_token = m.text
    try:
        thread = threading.Thread(target=start_bot, args=(bot_token,))
        thread.start()
        await m.answer('все гуд')
    except:
        await m.answer('щось пішло не так')



@router.message()
async def echo_handler(m: Message) -> None:
    await m.send_copy(chat_id=m.chat.id)


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(BOT_TOKEN, parse_mode='HTML')
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
