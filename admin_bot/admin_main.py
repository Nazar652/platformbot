import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, BaseFilter, Text
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


class PostConfiguringCallback(CallbackData, prefix='post'):
    channel: int
    action: str
    message_id: int


class PostFinalSettingCallback(CallbackData, prefix='post'):
    channel: int
    action: str
    message_id: int


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

    class NewPost(StatesGroup):
        writing_post = State()
        config_post = State()
        setting_post = State()

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

    @router.callback_query(Text("to_channels_menu"))
    async def to_channels_menu(query: CallbackQuery):
        m: Message = query.message
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
            await m.edit_text('Список каналів підключених до цього бота:', reply_markup=callback_markup)
        else:
            await m.edit_text('На даний момент до бота не підключено жоден канал')

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
                'callback_data': 'to_channels_menu'
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
    async def channel_post_action(query: CallbackQuery, callback_data: ChannelActionCallback, state: FSMContext):
        await state.update_data(callback_data=callback_data)
        await query.message.edit_text(text="Надішліть повідомлення яке хочете опублікувати на каналі")
        await state.set_state(NewPost.writing_post)

    @router.message(NewPost.writing_post)
    async def configuring_post(m: Message, state: FSMContext):
        data = await state.get_data()
        callback_data = data['callback_data']
        channel_id = callback_data.identifier
        channel_instance = Channel.get_instance(identifier=channel_id)
        actions_to_markup = []
        message_to_redact = await m.send_copy(chat_id=m.chat.id)
        message_instance = Post.create_instance(
            copy_message_id=message_to_redact.message_id,
            copy_chat_id=message_to_redact.chat.id,
            channel=channel_instance
        )
        await state.update_data(message_to_redact=message_to_redact, message_instance=message_instance)
        row = [
            {
                'text': 'Поділитися',
                'callback_data': PostConfiguringCallback(channel=channel_id, action='make_share',
                                                         message_id=message_to_redact.message_id).pack()
            },
            {
                'text': 'Автопідпис',
                'callback_data': PostConfiguringCallback(channel=channel_id, action='auto_signature',
                                                         message_id=message_to_redact.message_id).pack()
            }
        ]
        actions_to_markup.append(row)
        row = [
            {
                'text': 'Додати URL кнопки',
                'callback_data': PostConfiguringCallback(channel=channel_id, action='url_buttons',
                                                         message_id=message_to_redact.message_id).pack()
            },
            {
                'text': 'Додати коментарі',
                'callback_data': PostConfiguringCallback(channel=channel_id, action='comments',
                                                         message_id=message_to_redact.message_id).pack()
            }
        ]
        actions_to_markup.append(row)
        row = [
            {
                'text': 'Назад',
                'callback_data': ChannelCallback(identifier=channel_id).pack()
            },
            {
                'text': 'Продовжити',
                'callback_data': PostConfiguringCallback(channel=channel_id, action='continue',
                                                         message_id=message_to_redact.message_id).pack()
            }
        ]
        actions_to_markup.append(row)
        callback_markup = create_callback_markup(actions_to_markup)
        await m.answer(text="Налаштування поста", reply_markup=callback_markup)
        await state.update_data(message_to_redact=message_to_redact)
        await state.set_state(NewPost.config_post)

    @router.callback_query(PostConfiguringCallback.filter(F.action == 'make_share'), NewPost.config_post)
    async def share_button(query: CallbackQuery, callback_data: PostConfiguringCallback, state: FSMContext):
        data = await state.get_data()
        message_to_redact: Message = data['message_to_redact']
        channel_id = callback_data.channel
        markup = message_to_redact.reply_markup
        if markup:
            markup.inline_keyboard.append([InlineKeyboardButton(text='Поділитися', callback_data='share')])
        else:
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Поділитися', callback_data='share')]])
        message_to_redact = await message_to_redact.edit_reply_markup(reply_markup=markup)
        redact_markup = query.message.reply_markup
        redact_markup.inline_keyboard[0][0] = InlineKeyboardButton(
            text='Поділитися',
            callback_data=PostConfiguringCallback(channel=channel_id, action='remove_share',
                                                  message_id=message_to_redact.message_id).pack()
        )
        await query.message.edit_reply_markup(reply_markup=redact_markup)
        await state.update_data(message_to_redact=message_to_redact)
        await query.answer(text='Додано кнопку "Поділитися"', show_alert=False)

    @router.callback_query(PostConfiguringCallback.filter(F.action == 'remove_share'), NewPost.config_post)
    async def share_button(query: CallbackQuery, callback_data: PostConfiguringCallback, state: FSMContext):
        data = await state.get_data()
        message_to_redact: Message = data['message_to_redact']
        channel_id = callback_data.channel
        keyboard = message_to_redact.reply_markup.inline_keyboard
        del_i, del_j = 0, 0
        for i, row in enumerate(keyboard):
            for j, item in enumerate(row):
                if item.callback_data == 'share':
                    del_i, del_j = i, j
        keyboard[del_i].pop(del_j)
        print(keyboard)
        await message_to_redact.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        redact_markup = query.message.reply_markup
        redact_markup.inline_keyboard[0][0] = InlineKeyboardButton(
            text='Прибрати Поділитися',
            callback_data=PostConfiguringCallback(channel=channel_id, action='make_share',
                                                  message_id=message_to_redact.message_id).pack()
        )
        await query.message.edit_reply_markup(reply_markup=redact_markup)
        await query.answer(text='Вилучено кнопку "Поділитися"', show_alert=False)

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
