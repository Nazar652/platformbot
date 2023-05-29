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
from admin_bot.admin_main import start_bot

from database import *

router = Router()


class NewBot(StatesGroup):
    writing_bot_token = State()


def send_messages():
    print(123)


def start_send_messages():
    while True:
        send_messages()
        time.sleep(60)


async def start_admin_bot(bot_token, bot_model) -> bool:
    thread = threading.Thread(target=start_bot, args=(bot_token, bot_model))
    thread.start()
    time.sleep(1)
    if bot_model.is_executing:
        return True
    else:
        bot_model.delete_instance()
        return False


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
        if await start_admin_bot(bot_token, bot_model):
            await m.answer("Бот запущено")
        else:
            await m.answer("Невірний бот-токен")
    await state.clear()


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)

    # db.drop_tables(
    #     [User,
    #      BotModel,
    #      Channel,
    #      ChannelSubscriber,
    #      Post,
    #      CyclicPost,
    #      AutoSignature]
    # )
    subscriber_channel = Channel.subscribers.get_through_model()
    db.create_tables(
        [User,
         BotModel,
         Channel,
         ChannelSubscriber,
         Post,
         CyclicPost,
         AutoSignature,
         subscriber_channel],
        safe=True
    )

    # User.create_table(safe=True)
    # BotModel.create_table(safe=True)
    # Channel.create_table(safe=True)
    # ChannelSubscriber.create_table(safe=True)
    # Post.create_table(safe=True)
    # CyclicPost.create_table(safe=True)
    # AutoSignature.create_table(safe=True)
    for b in BotModel.get_all():
        await start_admin_bot(b.bot_token, b)

    thread = threading.Thread(target=start_send_messages)
    thread.start()

    bot = Bot(BOT_TOKEN, parse_mode='HTML')
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
