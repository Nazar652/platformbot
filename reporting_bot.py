import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import csv
import datetime

from peewee_database import *


bot_token = "5773290502:AAG_0g8_vTUuf64hK8NUq_4OfSWeXaNdpnM"
bot = Bot(token=bot_token)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_bot(message: types.Message):
    kb = [[types.KeyboardButton(text="get csv")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer("intro text", reply_markup=keyboard)


@dp.message(Command("get_csv"))
async def get_csv(message: types.Message):
    # TODO: connect to another bot
    chat_id = 1

    get_users = User.select().where(User.chat_id == chat_id)
    headers = ["id", "firstname", "lastname", "username"]
    file_name = f"{datetime.datetime.now().strftime('%Y-%m-%d')}_users.csv"
    with open(file_name, 'a',  encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow([user.id, user.firstname, user.lastname, user.username] for user in get_users)

    with open(file_name, 'rb') as f:
        await bot.send_document(message.chat.id,  f)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
