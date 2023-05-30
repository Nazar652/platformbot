import logging
import os
from PIL import Image, ImageDraw, ImageFont
import aiogram
import asyncio

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import BufferedInputFile, Message
import io


bot_token = '5773290502:AAFfOSXk2ltL_tM4QQsC9n8y424ocxps51o'
bot = aiogram.Bot(token=bot_token, parse_mode="HTML")
dp = aiogram.Dispatcher()


async def add_text_watermark(image_id, original_image, watermark_text):

    font = ImageFont.truetype('Roboto-Black.ttf', 15)
    image = Image.open(original_image)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    watermarked_file = f'img/watermarked_{image_id}.png'
    draw = ImageDraw.Draw(overlay)

    text_width, text_height = draw.textsize(watermark_text, font)
    width, height = image.size
    x = width / 2 - text_width / 2
    y = height - text_height - 300

    draw.text((x, y), watermark_text, (255, 255, 255, 255), font=font)

    result = Image.alpha_composite(image.convert("RGBA"), overlay.point(lambda p: p * 0.65))
    result.save(watermarked_file)

    return watermarked_file


async def add_img_watermark(original_image_id, original_image, watermark_image):
    transparency = 65
    watermarked_file = f'img/watermarked_{original_image_id}.png'

    base_img = Image.open(original_image)
    watermark = Image.open(watermark_image)

    if watermark.mode != 'RGBA':
        alpha = Image.new('L', watermark.size, 255)
        watermark.putalpha(alpha)

    watermark_size = (int(base_img.width / 5), int(base_img.height / 5))
    watermark = watermark.resize(watermark_size, Image.LANCZOS)

    position = (int(base_img.width / 2), int(base_img.height / 2))

    paste_mask = watermark.split()[3].point(lambda i: i * transparency / 100.)

    base_img.paste(watermark, position, mask=paste_mask)
    base_img.save(watermarked_file)

    return watermarked_file


class AddWatermark(StatesGroup):
    upload_image = State()
    watermark = State()
    confirm = State()


@dp.message(Command(commands=['upload_image']))
async def start_upload_image(m: Message,  state: FSMContext):
    await m.answer('send a image')
    await state.set_state(AddWatermark.upload_image)


@dp.message(AddWatermark.upload_image)
async def upload_image(m: Message, state: FSMContext):
    await state.update_data(original_image=m)
    await m.answer('send a watermark image or your watermark text')
    await state.set_state(AddWatermark.watermark)


# @dp.message(Command(commands=['watermark']))
# async def start_watermark(m: Message,  state: FSMContext):
#     await m.answer('send a watermark image or your watermark text')
#     await state.set_state(AddWatermark.watermark)


@dp.message(AddWatermark.watermark)
async def adding_watermark(m: Message, state: FSMContext):
    await state.update_data(watermark_data=m)

    original_image = await state.get_data()
    original_image = original_image["original_image"]
    image_data = original_image.photo[-1]
    original_image_path = f"img/{image_data.file_unique_id}.png"
    await bot.download(image_data, original_image_path)

    if m.text:
        watermark_text = m.text
        watermarked_file = await add_text_watermark(image_data.file_unique_id, original_image_path, watermark_text)
        os.remove(original_image_path)
    elif m.photo:
        watermark_image = m.photo[-1]
        watermark_image_path = f"img/{watermark_image.file_unique_id}.png"
        await bot.download(watermark_image, watermark_image_path)
        watermarked_file = await add_img_watermark(image_data.file_unique_id, original_image_path, watermark_image_path)
        os.remove(watermark_image_path)
    else:
        await m.answer('send a watermark image or your watermark text')
        return

    with open(watermarked_file, 'rb') as image_data:
        set_to_bytes = io.BytesIO(image_data.read())
        photo = BufferedInputFile(set_to_bytes.read(), filename=watermarked_file)
        await m.answer_photo(photo)

    os.remove(watermarked_file)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())



