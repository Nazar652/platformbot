import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, BaseFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import *


class ChannelForwarded(BaseFilter):
    async def __call__(self, message: Message) -> bool:  # [3]
        return bool(message.forward_from_chat)


class ChannelCallback(CallbackData, sep=':', prefix='channel'):
    identifier: int


class ChannelActionCallback(CallbackData, prefix='channel'):
    identifier: int
    action: str


def create_callback_markup(callback_queries: list[list[dict]]) -> InlineKeyboardMarkup:
    callback_markup: list[list[InlineKeyboardButton]] = []
    for row in callback_queries:
        row_markup = []
        for item in row:
            row_markup.append(InlineKeyboardButton(**item))
        callback_markup.append(row_markup)
    return InlineKeyboardMarkup(inline_keyboard=callback_markup)


async def main(bot_token, bot_model):
    router = Router()
    dp = Dispatcher()
    dp.include_router(router)

    class NewChannel(StatesGroup):
        adding_channel = State()

    # Message handling
    @router.message(Command(commands=["start"]))
    async def command_start(m: Message) -> None:
        await m.answer(f'Бот адміністратор.\n\nДодати канал: /addchannel\nСписок каналів: /channels')

    @router.message(Command(commands=["addchannel"]))
    async def command_start(m: Message, state: FSMContext) -> None:
        await m.answer(f'Перешліть повідомлення з каналу, в якому цей бот є адміном')
        await state.set_state(NewChannel.adding_channel)

    @router.message(NewChannel.adding_channel, ChannelForwarded())
    async def new_channel(m: Message, state: FSMContext) -> None:
        channel = m.forward_from_chat
        member = await bot.get_chat_member(chat_id=channel.id, user_id=bot_user.id)
        if Channel.get_instance(channel.id):
            await m.answer("Цей канал вже підключено до бота адміністратора")
        else:
            if member.status == 'administrator':
                await m.answer("Додано канал")
                channel_entity = Channel.get_instance(channel.id)
                if channel_entity:
                    await m.answer("Цей канал вже є в базі даних")
                else:
                    Channel.create_instance(
                        identifier=channel.id,
                        title=channel.title,
                        bot=BotModel.get_instance(identifier=bot_user.id)
                    )
            else:
                await m.answer("Бот не є адміністратором у цьому каналі")
        await state.clear()

    @router.message(Command(commands=['channels']))
    async def channels_list(m: Message) -> None:

        channels = Channel.get_join_instance(BotModel, BotModel.identifier == bot.id)
        if channels:
            channels_to_markup = []
            for c in channels:
                channels_to_markup.append(
                    [{
                        'text': c.title,
                        'callback_data': ChannelCallback(identifier=c.identifier).pack()
                    }]
                )
            callback_markup = create_callback_markup(channels_to_markup)
            await m.answer('Список каналів підключених до цього бота:', reply_markup=callback_markup)
        else:
            await m.answer('На даний момент до бота не підключено жоден канал')

    # Callback handling

    @router.callback_query(ChannelCallback.filter())
    async def channel_callback(query: CallbackQuery, callback_data: ChannelCallback):
        m: Message = query.message
        channel_instance = Channel.get_instance(identifier=callback_data.identifier)
        actions_to_markup = []
        row = [
            {
                'text': 'Опублікувати пост',
                'callback_data': ChannelActionCallback(identifier=callback_data.identifier, action='post').pack()
            },
            {
                'text': 'Автопідпис',
                'callback_data': ChannelActionCallback(
                    identifier=callback_data.identifier, action='autosignature').pack()
            }
        ]
        actions_to_markup.append(row)
        row = [
            {
                'text': 'Здійснити розсилку всім підписникам',
                'callback_data': ChannelActionCallback(identifier=callback_data.identifier, action='mailing').pack()
            }
        ]
        actions_to_markup.append(row)
        row = [
            {
                'text': 'Запланувати циклічний пост',
                'callback_data': ChannelActionCallback(identifier=callback_data.identifier, action='cyclicpost').pack()
            }
        ]
        actions_to_markup.append(row)
        row = [
            {
                'text': '⬅️ Назад',
                'callback_data': ChannelCallback(identifier=callback_data.identifier).pack()
            },
            {
                'text': 'Видалити канал',
                'callback_data': ChannelActionCallback(identifier=callback_data.identifier, action='delete').pack()
            }
        ]
        actions_to_markup.append(row)
        actions_markup = create_callback_markup(actions_to_markup)
        await m.edit_text(text=f"Канал {channel_instance.title}", reply_markup=actions_markup)

    @router.callback_query(ChannelActionCallback.filter(F.action == 'post'))
    async def channel_post_action(query: CallbackQuery, callback_data: ChannelActionCallback):
        await query.answer(text="гуд", show_alert=False)

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
