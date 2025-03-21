import logging
import sys
import traceback
from typing import List, Optional, Union
import discord
from discord.ext import commands
from discord.ui import Button
import requests

from src.core._cog_loader import CogLoader
from src.core.client import Client

class ConfirmLeaveServer(discord.ui.View):
    msg: discord.Message
    children: List[Button]
    value: Optional[bool]

    def __init__(self, author: Union[discord.User, discord.Member], server: discord.Guild):
        super().__init__()
        self.value = None
        self.author = author
        self.server = server

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.msg.edit(view=self)

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author.id:
            await interaction.response.send_message(f"I've left **{self.server.name}**.")
            self.value = True
            self.stop()
            for item in self.children:
                item.disabled = True
            await self.msg.edit(view=self)
        else:
            await interaction.response.send_message(f"You're not {self.author}. Go away!", ephemeral=True)

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author.id:
            await interaction.response.send_message(f"Ok! I'm not leaving **{self.server.name}**.")
            self.value = False
            self.stop()
            for item in self.children:
                item.disabled = True
            await self.msg.edit(view=self)
        else:
            await interaction.response.send_message(f"You're not {self.author}. Go away!", ephemeral=True)

class Core(commands.Cog):
    def __init__(self, bot: Client):
        self.bot = bot

    @commands.command(help='List the loaded & unloaded cogs.')
    @commands.is_owner()
    async def cogs(self, ctx: commands.Context):
        cogs = self.bot.get_cogs()
        # embeds
        title = f"{len(cogs['loaded'])} Cogs Loaded :"
        description = "{}".format(", ".join(sorted(cogs['loaded'])))
        load_cog = discord.Embed(
            title=title, description=description, color=0x1f8b4c)

        title = f"{len(cogs['unloaded']) } Cogs Unloaded :"

        description = "{}".format(", ".join(sorted(cogs['unloaded'])))

        unload_cog = discord.Embed(title=title, description=description, color=0x992e22)
        await ctx.send(embed=load_cog)
        await ctx.send(embed=unload_cog)

    @commands.command(help='Load a specific unloaded cog.')
    @commands.is_owner()
    async def load(self, ctx: commands.Context, extension: str):
        try:
            await self.bot.load_extension(f'{CogLoader.base_cog_import_path}{extension}')
            await ctx.send(f"`{extension}` loaded.")
        except Exception as error:
            tb_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            self.bot._last_error = tb_error
            self.bot._logger.error(tb_error)
            raise error

    @commands.command(help='Unload a specific loaded cog.')
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, extension: str):
        try:
            await self.bot.unload_extension(f'{CogLoader.base_cog_import_path}{extension}')
            await ctx.send(f"`{extension}` unloaded.")
        except Exception as error:
            tb_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            self.bot._last_error = tb_error
            self.bot._logger.error(tb_error)
            raise error

    @commands.command(help='Reload a specific cog.')
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, extension: str):
        try:
            await self.bot.reload_extension(f'{CogLoader.base_cog_import_path}{extension}')
            await ctx.send(f"`{extension}` reloaded.")
        except Exception as error:
            tb_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            self.bot._last_error = tb_error
            self.bot._logger.error(tb_error)
            raise error

    @commands.command(help='Stops the bot.')
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        await ctx.send("Shutting down...")
        
        session = self.bot.http._HTTPClient__session
        if session and not session.closed:
            await session.close()

        await ctx.bot.close()

    @commands.command(help='Synchronize the app commands with the Discord API.')
    @commands.is_owner()
    async def slashsync(self, ctx: commands.Context, guild: Optional[discord.Guild] = None):
        if not guild:
            guild = self.bot.get_main_guild()

        msg = await ctx.send("Les commandes d'application sont en cours de synchronisation..." + 
                            "\nCela peut prendre quelques temps.")
        
        await self.bot.tree.sync(guild=discord.Object(id=guild.id))
        await msg.edit(content="Les commandes d'application ont bien été synchronisées. ✅")

    @commands.group(help='List all the servers where the bot is in.')
    @commands.is_owner()
    async def servers(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            servers = sorted(self.bot.guilds, key=lambda s: s.name.lower())
            msg = "\n".join(f"- {server.name} :`{server.id}`" for server in servers)

            await ctx.send(msg)

    @servers.command(help='Making the bot leave a specific server.')
    @commands.is_owner()
    async def leave(self, ctx: commands.Context, server: discord.Guild):

        if server in self.bot.guilds:
            view = ConfirmLeaveServer(ctx.author, server)
            view.msg = await ctx.send(content=f"Do you want me to leave **{server.name}**?", view=view)
            await view.wait()
        else:
            await ctx.send("I must be in the server before leaving it.")

    @commands.group(name="set", help="Various settings for the bot")
    @commands.is_owner()
    async def _set(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @_set.command(help="Set the bot's avatar")
    @commands.is_owner()
    async def avatar(self, ctx: commands.Context, url: str = None):
        if len(ctx.message.attachments) > 0:
            data = await ctx.message.attachments[0].read()
        elif url != None:
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]

            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.content
            except requests.exceptions.InvalidURL:
                return await ctx.reply("That URL is invalid.")
            except requests.exceptions.RequestException:
                return await ctx.reply("Something went wrong while trying to get the image.")
        else:
            await ctx.send_help()
            return

        try:
            async with ctx.typing():
                await self.bot.user.edit(avatar=data)
        except discord.HTTPException:
            await ctx.reply("Failed. Remember that you can edit my avatar up to two time a hour.\n"
                            "The URL or attachment must be a valid image in either JPG or PNG format.")
        except discord.InvalidArgument:
            await ctx.reply("JPG / PNG format only.")
        else:
            await ctx.reply("Done.")

    @_set.command(name="game", help="Set the bot 'Playing to...'")
    @commands.is_owner()
    async def _game(self, ctx: commands.Context, *, game: str = None):
        if game:
            if len(game) > 128:
                await ctx.reply("The maximum length of game descriptions is 128 characters.")
                return
            game = discord.Game(name=game)
        else:
            game = None
        status = self.bot.guilds[0].me.status if len(self.bot.guilds) > 0 else discord.Status.online
        await self.bot.change_presence(status=status, activity=game)
        if game:
            await ctx.reply("Status set to ``Playing {game.name}``.".format(game=game))
        else:
            await ctx.reply("Game cleared.")

    @_set.command(name="listening", help="Set the bot 'Listening to...'")
    @commands.is_owner()
    async def _listening(self, ctx: commands.Context, *, listening: str = None):
        status = self.bot.guilds[0].me.status if len(self.bot.guilds) > 0 else discord.Status.online
        if listening:
            if len(listening) > 128:
                await ctx.reply("The maximum length of listening descriptions is 128 characters.")
                return
            activity = discord.Activity(name=listening, type=discord.ActivityType.listening)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.reply("Status set to ``Listening to {listening}``.".format(listening=listening))
        else:
            await ctx.reply("Listening cleared.")

    @_set.command(name="watching", help="Set the bot 'Watching ...'")
    @commands.is_owner()
    async def _watching(self, ctx: commands.Context, *, watching: str = None):
        status = self.bot.guilds[0].me.status if len(self.bot.guilds) > 0 else discord.Status.online
        if watching:
            if len(watching) > 128:
                await ctx.reply("The maximum length of watching descriptions is 128 characters.")
                return
            activity = discord.Activity(name=watching, type=discord.ActivityType.watching)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.reply("Status set to ``Watching {watching}``.".format(watching=watching))
        else:
            await ctx.reply("Watching cleared.")

    @_set.command(name="competing", help="Set the bot 'Competing to...'")
    @commands.is_owner()
    async def _competing(self, ctx: commands.Context, *, competing: str = None):
        status = self.bot.guilds[0].me.status if len(self.bot.guilds) > 0 else discord.Status.online
        if competing:
            if len(competing) > 128:
                await ctx.reply("The maximum length of competing descriptions is 128 characters.")
                return
            activity = discord.Activity(name=competing, type=discord.ActivityType.competing)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.reply("Status set to ``Competing in {competing}``.".format(competing=competing))
        else:
            await ctx.reply("Competing cleared.")

    @_set.command(name="status", help="Set the bot's status")
    @commands.is_owner()
    async def _status(self, ctx: commands.Context, *, status: str = 'online'):
        statuses = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }

        game = self.bot.guilds[0].me.activity if len(self.bot.guilds) > 0 else None
        try:
            status = statuses[status.lower()]
        except KeyError:
            await ctx.reply(f"Status must be one of the following: {', '.join([key for key in statuses])}")
        else:
            await ctx.bot.change_presence(status=status, activity=game)
            await ctx.reply("Status changed to {}.".format(status))

    @_set.command(name="stream", help="Set the bot 'Streaming...'")
    @commands.is_owner()
    async def _stream(self, ctx: commands.Context, streamer=None, *, stream_title=None):
        status = self.bot.guilds[0].me.status if len(self.bot.guilds) > 0 else None

        if stream_title:
            stream_title = stream_title.strip()
            if "twitch.tv/" not in streamer:
                streamer = "https://www.twitch.tv/" + streamer
            if len(streamer) > 511:
                await ctx.reply("The maximum length of the streamer url is 511 characters.")
                return
            if len(stream_title) > 128:
                await ctx.reply("The maximum length of the stream title is 128 characters.")
                return
            activity = discord.Streaming(url=streamer, name=stream_title)
            await ctx.bot.change_presence(status=status, activity=activity)
        elif streamer is not None:
            await ctx.send_help()
            return
        else:
            await ctx.bot.change_presence(activity=None, status=status)
        await ctx.send("Done.")

    @commands.command(aliases=['tb'], help='Display the last traceback.')
    @commands.is_owner()
    async def traceback(self, ctx: commands.Context):
        if self.bot._last_error:
            await ctx.reply(f"```py\n{self.bot._last_error}\n```")
        else:
            await ctx.reply("No exception has occurred yet.")

async def setup(bot):
    await bot.add_cog(Core(bot))
