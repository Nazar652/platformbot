import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import datetime

from peewee_database import *

bot_token = "5773290502:AAG_0g8_vTUuf64hK8NUq_4OfSWeXaNdpnM"
bot = Bot(token=bot_token)
dp = Dispatcher()


@dp.chat_join_request()
async def approve_chat_join_request(request: types.ChatJoinRequest):
    user_data = request.from_user
    await bot.approve_chat_join_request(request.chat.id, user_data.id)
    await bot.send_message(chat_id=user_data.id, text="welcome message")

    # TODO: add user to database
    user = User(identifier=user_data.id, firstaname=user_data.first_name, lastname=user_data.last_name,
                username=user_data.username,  chat_id=request.chat.id)
    user.save()


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
        message_text = await state.get_data()
        ScheduleMessage(send_date=date, text=message_text["message_content"])
        await message.answer(text="schedule created successfully")
        await state.clear()
    except ValueError:
        await message.answer(text="invalid date format. please use DD:MM:YYYY HH:MM format.")


async def send_scheduled_messages():
    while True:
        current_time = datetime.datetime.now().time()

        send_date = ScheduleMessage.select().where(ScheduleMessage.send_date <= current_time)
        # TODO потрібно отримати ІД чату в якому бот адмін
        users = User.select().where(User.chat_id == 1)
        chunks = [users[i:i + 1000] for i in range(0, len(users), 1000)]
        for chunk in chunks:
            for user in chunk:
                await bot.send_message(user.identifier, send_date.text)
        ScheduleMessage.delete().where(ScheduleMessage.send_date == send_date)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
