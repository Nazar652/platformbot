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


bot_token = ''
bot = aiogram.Bot(token=bot_token, parse_mode="HTML")
dp = aiogram.Dispatcher()

telegraph_api = Telegraph()
access_token = telegraph_api.createAccount('telegraph_bot')["access_token"]
telegraph = Telegraph(access_token)


@dp.message(Command('start'))
async def start(message: aiogram.types.Message):
    await message.reply("send img")


async def download_file(save_path: str, file_url: str):
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            file.write(response.content)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error occurred: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Error connecting to the server: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


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

    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}"

    await download_file(image_path, file_url)

    hidden_link = await upload_file(image_path)
    await delete_file(image_path)
    await message.answer(f"some text: {hidden_link}")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
