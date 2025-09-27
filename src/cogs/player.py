import lavalink
import os
from discord.ext import commands


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'lavalink'):
            lavalink_host = os.getenv('LAVALINK_HOST', 'localhost')
            lavalink_port = int(os.getenv('LAVALINK_PORT', '2333'))
            lavalink_password = os.getenv('LAVALINK_PASSWORD', 'youshallnotpass')
            
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(host=lavalink_host, port=lavalink_port, password=lavalink_password,
                                  region='us', name='default-node')

        self.lavalink: lavalink.Client = bot.lavalink
        self.lavalink.add_event_hooks(self)
