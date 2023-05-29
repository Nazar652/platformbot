import asyncio
import logging
import string

import aiogram
import requests
from aiogram.filters import Command
from telegraphapi import Telegraph
from aiogram.utils import markdown
import random

import os


bot_token = '5773290502:AAFfOSXk2ltL_tM4QQsC9n8y424ocxps51o'
bot = aiogram.Bot(token=bot_token, parse_mode="HTML")
dp = aiogram.Dispatcher()

telegraph_api = Telegraph()
access_token = telegraph_api.createAccount('telegraph_bot')["access_token"]
telegraph = Telegraph(access_token)


@dp.message(Command('start'))
async def start(message: aiogram.types.Message):
    await message.reply("send img")


async def upload_file(image_path: str) -> str:
    with open(image_path, 'rb') as f:
        response_post = requests.post("https://telegra.ph/upload", files={'file': f})
        img_link = response_post.json()[0]['src']
        hidden_link = markdown.hide_link(f"https://telegra.ph/{img_link}")
        return hidden_link


async def delete_file(image_path: str):
    os.remove(image_path)


@dp.message()
async def process_photo(message: aiogram.types.Message):
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    image_path = f"img/{random_string}.jpg"

    await bot.download(message.photo[-1],  image_path)

    hidden_link = await upload_file(image_path)
    await delete_file(image_path)
    await message.answer(f"some text: {hidden_link}")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
