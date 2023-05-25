import asyncio
import logging
import threading
import time

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from config import BOT_TOKEN
from admin_bot import start_bot

from database import *

router = Router()


class NewBot(StatesGroup):
    writing_bot_token = State()


@router.message(Command(commands=["start"]))
async def command_start(m: Message) -> None:
    user = m.from_user
    if not User.get_instance(user.id):
        User.create_instance(
                identifier=user.id,
                firstname=user.first_name,
                lastname=user.last_name,
                username=user.username
            )
    await m.answer(f'Привітальне повідомлення\nСтворити бота: /newbot')


@router.message(Command(commands=["newbot"]))
async def command_new_bot(m: Message, state: FSMContext) -> None:
    await m.answer(f'Надішліть бот токен')
    await state.set_state(NewBot.writing_bot_token)


@router.message(NewBot.writing_bot_token)
async def new_bot_token(m: Message, state: FSMContext) -> None:
    bot_token = m.text
    if BotModel.get_instance(bot_token=bot_token):
        await m.answer("Бот з таким токеном вже є у базі даних")
    else:
        bot_model = BotModel.create_instance(
            identifier=0,
            name='',
            username='',
            bot_token=bot_token,
            is_executing=True,
            user=User.get_instance(m.from_user.id)
        )
        thread = threading.Thread(target=start_bot, args=(bot_token, bot_model))
        thread.start()
        time.sleep(1)
        if bot_model.is_executing:
            await m.answer("Бот запущено")
        else:
            await m.answer("Невірний бот-токен")
            bot_model.delete_instance()
    await state.clear()


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)

    db.drop_tables((User, BotModel, Channel))
    User.create_table(safe=True)
    BotModel.create_table(safe=True)
    Channel.create_table(safe=True)
    bot = Bot(BOT_TOKEN, parse_mode='HTML')
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())