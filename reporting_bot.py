import asyncio
import logging
import threading

from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
import csv
import datetime

from peewee_database import *

bot_token = "6083919093:AAFrGH05-QUcnBr_T78fKNWpr5EPlhaCyc0"
bot = Bot(token=bot_token)
dp = Dispatcher()
app = Flask(__name__)


@dp.message(Command("start"))
async def start_bot(message: types.Message):
    kb = [[types.KeyboardButton(text="report data")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer("intro text", reply_markup=keyboard)


@app.route('/api/get/userdata', methods=['GET'])
def write_json():
    with app.app_context():
        data = db.get_all()  # TODO
        response_data = []
        for user in data:
            response_data.append({
                'id': user.identifier,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'username': user.username,
                'channel_id': user.channel_id
            })

        return jsonify(response_data)


@dp.message(Text("report data"))
async def get_csv(message: types.Message):
    write_json()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=app.run)
    flask_thread.start()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
