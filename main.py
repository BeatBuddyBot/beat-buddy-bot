import asyncio
import os

from dotenv import load_dotenv

from src.bot import bot

load_dotenv()

if __name__ == "__main__":
    asyncio.run(bot.start(os.getenv("DISCORD_BOT_TOKEN")))
