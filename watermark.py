import logging
import os
from PIL import Image, ImageDraw, ImageFont
import aiogram
import asyncio
from aiogram.types import BufferedInputFile
import io


bot_token = '5773290502:AAFfOSXk2ltL_tM4QQsC9n8y424ocxps51o'
bot = aiogram.Bot(token=bot_token, parse_mode="HTML")
dp = aiogram.Dispatcher()


async def add_text_watermark(image_title, original_image, watermark_text):

    font = ImageFont.truetype('Roboto-Black.ttf', 15)
    image = Image.open(original_image)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    watermarked_file = f'img/watermarked_{image_title}.png'
    draw = ImageDraw.Draw(overlay)

    text_width, text_height = draw.textsize(watermark_text, font)
    width, height = image.size
    x = width / 2 - text_width / 2
    y = height - text_height - 300

    draw.text((x, y), watermark_text, (255, 255, 255, 255), font=font)

    result = Image.alpha_composite(image.convert("RGBA"), overlay.point(lambda p: p * 0.65))
    result.save(watermarked_file)

    return watermarked_file


async def add_img_watermark(random_string, original_img, watermark_img):
    transparency = 40
    watermarked_file = f'img/watermarked_{random_string}.png'

    base_img = Image.open(original_img)
    watermark = Image.open(watermark_img)

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


@dp.message()
async def process_photo(message: aiogram.types.Message):

    image_title = message.photo[-1].file_unique_id  # PLACEHOLDER already had image before run this part of script
    original_image_path = f"img/{image_title}.png"  # PLACEHOLDER already had image before run this part of script
    await bot.download(message.photo[-1],
                       original_image_path)  # PLACEHOLDER already had image before run this part of script

    watermarked_file = await add_img_watermark(image_title, original_image_path, watermark_img='2.png')
    # watermarked_file = await add_text_watermark(image_title, original_image_path, watermark_text='watermark')

    with open(watermarked_file, 'rb') as image_data:
        set_to_bytes = io.BytesIO(image_data.read())
        photo = BufferedInputFile(set_to_bytes.read(), filename=watermarked_file)
        await message.answer_photo(photo)

    os.remove(watermarked_file)
    os.remove(original_image_path)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())



