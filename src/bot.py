import json
import logging

import aioredis
import discord
from discord.ext.commands import Bot

from src.cogs.player import MusicPlayer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)
bot = Bot(command_prefix="!", intents=discord.Intents.all())


async def player_listener():
    redis = aioredis.from_url("redis://host.docker.internal")
    pubsub = redis.pubsub()
    await pubsub.subscribe("bot_player")

    async for message in pubsub.listen():
        try:
            if message["type"] == "message":
                data = json.loads(message["data"])
                action = data.pop("action")
                func = getattr(bot.cogs["MusicPlayer"], action, None)
                await func(**data)
        except Exception as e:
            logger.exception(e)


@bot.event
async def on_ready():
    await bot.add_cog(MusicPlayer(bot))
    bot.loop.create_task(player_listener())
    logger.warning(f'Bot {bot.user} is online')
