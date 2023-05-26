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
    kb = [[types.KeyboardButton(text="get csv")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer("intro text", reply_markup=keyboard)


@app.route('/api/get/userdata', methods=['GET'])
def write_json():
    with app.app_context():
        response_data = []
        for user in get_users:
            response_data.append({
                'id': user.identifier,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'username': user.username
            })

        return jsonify(response_data)


@dp.message(Text("get csv"))
async def get_csv(message: types.Message):
    # TODO: connect to another bot
    chat_id = -1001779692541
    get_users = User.select().where(User.chat_id == chat_id)
    write_json(get_users)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=app.run)
    flask_thread.start()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
