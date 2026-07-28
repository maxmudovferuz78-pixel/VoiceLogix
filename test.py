import asyncio
from aiogram import Bot
from config import BOT_TOKEN

async def main():
    bot = Bot(BOT_TOKEN)
    me = await bot.get_me()
    print(me)

asyncio.run(main())