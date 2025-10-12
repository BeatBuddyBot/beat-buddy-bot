import json
import logging

import aioredis
import discord
from discord.ext.commands import Bot

from src.cogs.player import MusicPlayer

logger = logging.getLogger(__name__)
bot = Bot(command_prefix="!", intents=discord.Intents.all())


async def player_listener():
    redis = aioredis.from_url("redis://localhost")
    pubsub = redis.pubsub()
    await pubsub.subscribe("bot_player")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            action = data.pop("action")
            func = getattr(bot.cogs["MusicPlayer"], action, None)
            await func(**data)


@bot.event
async def on_ready():
    bot.loop.create_task(player_listener())
    await bot.add_cog(MusicPlayer(bot))
    logger.warning(f'Bot {bot.user} is online')
