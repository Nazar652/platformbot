import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command(commands=["start"]))
async def command_start(m: Message) -> None:
    await m.answer(f'Привітальне повідомлення')


async def main(bot_token) -> None:
    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(bot_token, parse_mode='HTML')
    await dp.start_polling(bot)


def start_bot(bot_token):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(main(bot_token))
    loop.close()



