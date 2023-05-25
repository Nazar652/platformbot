import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from database import *


class ChannelForwarded(BaseFilter):
    async def __call__(self, message: Message) -> bool:  # [3]
        return bool(message.forward_from_chat)


async def main(bot_token, bot_model):
    router = Router()
    dp = Dispatcher()
    dp.include_router(router)

    class NewChannel(StatesGroup):
        adding_channel = State()

    @router.message(Command(commands=["start"]))
    async def command_start(m: Message) -> None:
        await m.answer(f'Бот адміністратор. Додати канал:\n/addchannel')

    @router.message(Command(commands=["addchannel"]))
    async def command_start(m: Message, state: FSMContext) -> None:
        await m.answer(f'Перешліть повідомлення з каналу, в якому цей бот є адміном')
        await state.set_state(NewChannel.adding_channel)

    @router.message(NewChannel.adding_channel, ChannelForwarded())
    async def new_channel(m: Message, state: FSMContext) -> None:
        channel = m.forward_from_chat
        print(channel)
        member = await bot.get_chat_member(chat_id=channel.id, user_id=bot_user.id)
        if member.status == 'administrator':
            await m.answer("Додано канал")
            channel_entity = Channel.get_instance(channel.id)
            if channel_entity:
                await m.answer("Цей канал вже є в базі даних")
            else:
                Channel.create_instance(
                    identifier=channel.id,
                    title=channel.title,
                    bot=BotModel.get_instance(bot_user.id)
                )
        else:
            await m.answer("Бот не є адміністратором у цьому каналі")
        await state.clear()

    try:
        bot = Bot(bot_token, parse_mode='HTML')
        bot_user = await bot.get_me()
        bot_model.identifier = bot_user.id
        bot_model.name = bot_user.first_name
        bot_model.username = bot_user.username
        bot_model.save()
        await dp.start_polling(bot)
    except:
        bot_model.is_executing = False
        bot_model.save()


def start_bot(bot_token, bot_model):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(main(bot_token, bot_model))
    loop.close()
