import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message


async def main(bot_token, bot_model):
    router = Router()
    dp = Dispatcher()
    dp.include_router(router)

    @router.message(Command(commands=["start"]))
    async def command_start(m: Message) -> None:
        await m.answer(f'Привітальне повідомлення')

    try:
        bot = Bot(bot_token, parse_mode='HTML')
        await dp.start_polling(bot)
    except:
        bot_model.is_executing = False
        bot_model.save()


def start_bot(bot_token, bot_model):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(main(bot_token, bot_model))
    loop.close()
