import asyncio
import logging
import threading
import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import datetime

from peewee_database import *

bot_token = "5773290502:AAGYpYkNB2ir3SoUZPlrfLNdgTEeOmjbm4w"
bot = Bot(token=bot_token)
dp = Dispatcher()


@dp.chat_join_request()
async def approve_chat_join_request(request: types.ChatJoinRequest):
    user_data = request.from_user

    await bot.approve_chat_join_request(request.chat.id, user_data.id)
    await bot.send_message(chat_id=user_data.id, text="welcome message")

    if not User.select().where(User.identifier == user_data.id):
        user = await User(identifier=user_data.id, firstname=user_data.first_name, lastname=user_data.last_name,
                          username=user_data.username,  chat_id=request.chat.id)
        await user.save()


class ScheduleMessages(StatesGroup):
    message = State()
    post_date = State()


@dp.message(Command("schedule_message"))
async def message_content(message: types.Message, state: FSMContext):
    await message.answer(text="write content")
    await state.set_state(ScheduleMessages.message)


@dp.message(ScheduleMessages.message)
async def select_date(message: types.Message, state: FSMContext):
    await message.answer(text="write post date (in DD:MM:YYYY HH:MM format)")
    await state.update_data(message_content=message.text)
    await state.set_state(ScheduleMessages.post_date)


@dp.message(ScheduleMessages.post_date)
async def save_date(message: types.Message, state: FSMContext):
    date_str = message.text.strip()
    try:
        date = datetime.datetime.strptime(date_str, "%d:%m:%Y %H:%M")
        if date < datetime.datetime.now():
            await message.answer(text="date can't be in the past")
            return
        message_text = await state.get_data()
        schedule_message = ScheduleMessage(send_date=date, text=message_text["message_content"])
        schedule_message.save()
        await message.answer(text="schedule created successfully")
        await state.clear()
    except ValueError:
        await message.answer(text="invalid date format. please use DD:MM:YYYY HH:MM format.")


async def send_message(send_date):
    users = User.select().where(User.chat_id == -1001779692541)
    chunks = [users[i:i + 1000] for i in range(0, len(users), 1000)]

    for chunk in chunks:
        for user in chunk:
            await bot.send_message(user.identifier, send_date.text)
            time.sleep(1)


async def send_scheduled_messages():
    while True:
        current_time = datetime.datetime.now()
        send_dates = ScheduleMessage.select().where(ScheduleMessage.send_date <= current_time)
        for send_date in send_dates:
            await send_message(send_date)
            ScheduleMessage.delete().where(ScheduleMessage.send_date == send_date)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    # TODO розібратися чому не викликає
    thread = threading.Thread(target=send_scheduled_messages)
    thread.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
