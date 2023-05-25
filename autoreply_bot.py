import asyncio
from aiogram import Bot, Dispatcher, types

bot_token = "5773290502:AAHdspzp-nq2g_mdV3eg4Uk0n5ikvNRxS6s"
bot = Bot(token=bot_token)
dp = Dispatcher()


@dp.chat_join_request()
async def approve_chat_join_request(request: types.ChatJoinRequest):
    print(2)
    await bot.approve_chat_join_request(request.chat.id, request.from_user.id)

    await bot.send_message(chat_id=request.from_user.id, text="welcome message")


async def main():
    print(1)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
