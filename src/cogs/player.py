import os

import discord
import lavalink
from discord.ext import commands
from lavalink import ClientError, LoadType


class LavalinkVoiceClient(discord.VoiceProtocol):

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        if not hasattr(self.client, 'lavalink'):
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(host='localhost', port=2333, password='youshallnotpass',
                                          region='us', name='default-node')

        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        channel_id = data['channel_id']

        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))

        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }

        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False,
                      self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        if not force and not player.is_connected:
            return

        await self.channel.guild.change_voice_state(channel=None)

        player.channel_id = None
        await self._destroy()

    async def _destroy(self):
        self.cleanup()

        if self._destroyed:
            return

        self._destroyed = True

        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
        except ClientError:
            pass


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
        self.guild = bot.get_guild(int(os.getenv("DISCORD_GUILD_ID")))
        self.channel = bot.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
        self.voice_channel = bot.get_channel(int(os.getenv("DISCORD_VOICE_CHANNEL_ID")))
        self.author = self.guild.get_member(int(os.getenv("DISCORD_AUTHOR_ID")))

    async def create_player(self):
        if self.channel.guild is None:
            raise commands.NoPrivateMessage()

        player = self.lavalink.player_manager.create(self.channel.guild.id)

        voice_client = self.guild.voice_client

        if voice_client is None:
            permissions = self.voice_channel.permissions_for(self.guild.get_member(self.bot.user.id))

            if not permissions.connect or not permissions.speak:
                raise self.channel.send('I need the `CONNECT` and `SPEAK` permissions.')

            if self.voice_channel.user_limit > 0:
                if len(self.voice_channel.members) >= self.voice_channel.user_limit and not self.bot.guild_permissions.move_members:
                    raise self.channel.send('Your voice channel is full!')

            player.store('channel', self.channel.id)
            await self.voice_channel.connect(cls=LavalinkVoiceClient)
        elif voice_client.channel.id != self.voice_channel.id:
            raise self.channel.send('You need to be in my voicechannel.')

        return True

    async def play(self, urls):
        await self.create_player()

        player = self.bot.lavalink.player_manager.get(self.channel.guild.id)

        for url in urls:
            results = await player.node.get_tracks(url)

            embed = discord.Embed(color=discord.Color.blurple())

            if results.load_type == LoadType.EMPTY:
                return await self.channel.send("I couldn'\t find any tracks for that query.")
            elif results.load_type == LoadType.PLAYLIST:
                tracks = results.tracks

                for track in tracks:
                    track.extra["requester"] = self.author.id
                    player.add(track=track)

                embed.title = 'Playlist Enqueued!'
                embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
            else:
                track = results.tracks[0]
                embed.title = 'Track Enqueued'
                embed.description = f'[{track.title}]({track.uri})'
                track.extra["requester"] = self.author.id

                player.add(track=track)

            await self.channel.send(embed=embed)

        if not player.is_playing:
            await player.play()

    async def stop(self):
        player = self.bot.lavalink.player_manager.get(self.channel.guild.id)
        await player.stop()

    async def skip(self):
        player = self.bot.lavalink.player_manager.get(self.channel.guild.id)
        await player.skip()

    async def pause(self):
        player = self.bot.lavalink.player_manager.get(self.channel.guild.id)
        await player.set_pause(not player.paused)

    async def repeat(self):
        player = self.bot.lavalink.player_manager.get(self.channel.guild.id)

        if player.loop == player.LOOP_NONE:
            player.loop = player.LOOP_QUEUE
        elif player.loop == player.LOOP_QUEUE:
            player.loop = player.LOOP_SINGLE
        elif player.loop == player.LOOP_SINGLE:
            player.loop = player.LOOP_NONE

        await self.channel.send(player.loop)
