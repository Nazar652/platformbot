import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN


router = Router()


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
