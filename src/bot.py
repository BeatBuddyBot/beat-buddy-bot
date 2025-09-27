import logging
import discord
from discord.ext.commands import Bot

from src.cogs.player import MusicPlayer

logger = logging.getLogger(__name__)
bot = Bot(command_prefix="!", intents=discord.Intents.all())


@bot.event
async def on_ready():
    await bot.add_cog(MusicPlayer(bot))
    logger.warning(f'Bot {bot.user} is online')
