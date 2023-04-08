import discord
from discord.ext import commands
import os
import sys
import datetime
import time
import aiohttp

from dotenv import load_dotenv
load_dotenv()
POWI_GUILD_ID = os.getenv('POWI_GUILD_ID')

class ConfirmLeaveServer(discord.ui.View):
    def __init__(self, author, server):
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
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def cogs(self, ctx):
        loaded, unloaded = await self.bot.get_cogs()
        if not unloaded:
            unloaded = ["None"]
        # embeds
        title = f"{len(loaded)} Cogs Loaded :"
        description = "{}".format(", ".join(sorted(loaded)))
        load_cog = discord.Embed(
            title=title, description=description, color=0x73b504)

        if unloaded[0] == "None":
            title = "0 Cog Unloaded :"
        else:
            title = f"{len(unloaded) } Cogs Unloaded :"

        description = "{}".format(", ".join(sorted(unloaded)))

        unload_cog = discord.Embed(title=title, description=description, color=0xFF5733)
        await ctx.send(embed=load_cog)
        await ctx.send(embed=unload_cog)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension):
        try:
            await self.bot.load_extension(f'cogs.{extension}')
            await ctx.send(f"`{extension}` loaded.")
        except Exception as e:
            error = str(e).replace("'", "`").replace("cogs.", "")
            await ctx.send(error)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:
            await self.bot.unload_extension(f'cogs.{extension}')
            await ctx.send(f"`{extension}` unloaded.")
        except Exception as e:
            error = str(e).replace("'", "`").replace("cogs.", "")
            print(error)
            await ctx.send(error)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, extension):
        try:
            await self.bot.reload_extension(f'cogs.{extension}')
            await ctx.send(f"`{extension}` reloaded.")
        except Exception as e:
            error = str(e).replace("'", "`").replace("cogs.", "")
            await ctx.send(error)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("Shutting down...")
        await ctx.bot.close()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def slashsync(self, ctx):
        msg = await ctx.send("Les commandes d'application sont en cours de synchronisation..." + 
                            "\nCela peut prendre quelques temps.")
        await ctx.bot.tree.sync(guild=discord.Object(id=POWI_GUILD_ID))
        await msg.edit(content="Les commandes d'application ont bien été synchronisées. ✅")

    @commands.group(hidden=True)
    @commands.is_owner()
    async def servers(self, ctx):
        if ctx.invoked_subcommand is None:
            servers = sorted(self.bot.guilds, key=lambda s: s.name.lower())
            msg = "\n".join(f"- {server.name} :`{server.id}`" for server in servers)

            await ctx.send(msg)

    @servers.command(hidden=True)
    @commands.is_owner()
    async def leave(self, ctx, server: discord.Guild):

        if server in self.bot.guilds:
            view = ConfirmLeaveServer(ctx.author, server)
            view.msg = await ctx.send(content=f"Do you want me to leave **{server.name}**?", view=view)
            await view.wait()
        else:
            await ctx.send("I must be in the server before leaving it.")

    @commands.group(name="set", help="Various settings for the bot")
    @commands.is_owner()
    async def _set(self, ctx):
        pass

    @_set.command(help="Set the bot's avatar")
    @commands.is_owner()
    async def avatar(self, ctx, url: str = None):
        if len(ctx.message.attachments) > 0:
            data = await ctx.message.attachments[0].read()
        elif url != None:
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as r:
                        data = await r.read()
                except aiohttp.InvalidURL:
                    return await ctx.send("That URL is invalid.")
                except aiohttp.ClientError:
                    return await ctx.send("Somehting went wrong while trying to get the image.")
        else:
            await ctx.send_help()
            return

        try:
            async with ctx.typing():
                await ctx.bot.user.edit(avatar=data)
        except discord.HTTPException:
            await ctx.send("Failed. Remember that you can edit my avatar up to two time a hour.\n"
                            "The URL or attachment must be a valid image in either JPG or PNG format.")
        except discord.InvalidArgument:
            await ctx.send("JPG / PNG format only.")
        else:
            await ctx.send("Done.")

    @_set.command(name="game", help="Set the bot 'Playing to...'")
    @commands.is_owner()
    async def _game(self, ctx, *, game: str = None):
        if game:
            if len(game) > 128:
                await ctx.send("The maximum length of game descriptions is 128 characters.")
                return
            game = discord.Game(name=game)
        else:
            game = None
        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        await ctx.bot.change_presence(status=status, activity=game)
        if game:
            await ctx.send("Status set to ``Playing {game.name}``.".format(game=game))
        else:
            await ctx.send("Game cleared.")

    @_set.command(name="listening", help="Set the bot 'Listening to...'")
    @commands.is_owner()
    async def _listening(self, ctx, *, listening: str = None):
        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        if listening:
            if len(listening) > 128:
                await ctx.send("The maximum length of listening descriptions is 128 characters.")
                return
            activity = discord.Activity(name=listening, type=discord.ActivityType.listening)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.send("Status set to ``Listening to {listening}``.".format(listening=listening))
        else:
            await ctx.send("Listening cleared.")

    @_set.command(name="watching", help="Set the bot 'Watching ...'")
    @commands.is_owner()
    async def _watching(self, ctx, *, watching: str = None):
        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        if watching:
            if len(watching) > 128:
                await ctx.send("The maximum length of watching descriptions is 128 characters.")
                return
            activity = discord.Activity(name=watching, type=discord.ActivityType.watching)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.send("Status set to ``Watching {watching}``.".format(watching=watching))
        else:
            await ctx.send("Watching cleared.")

    @_set.command(name="competing", help="Set the bot 'Competing to...'")
    @commands.is_owner()
    async def _competing(self, ctx, *, competing: str = None):
        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        if competing:
            if len(competing) > 128:
                await ctx.send("The maximum length of competing descriptions is 128 characters.")
                return
            activity = discord.Activity(name=competing, type=discord.ActivityType.competing)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.send("Status set to ``Competing in {competing}``.".format(competing=competing))
        else:
            await ctx.send("Competing cleared.")

    @_set.command(name="status", help="Set the bot's status")
    @commands.is_owner()
    async def _status(self, ctx, *, status: str = None):
        statuses = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }

        game = ctx.bot.guilds[0].me.activity if len(ctx.bot.guilds) > 0 else None
        try:
            status = statuses[status.lower()]
        except KeyError:
            await ctx.send_help()
        else:
            await ctx.bot.change_presence(status=status, activity=game)
            await ctx.send("Status changed to {}.".format(status))

    @_set.command(name="stream", help="Set the bot 'Streming...'")
    @commands.is_owner()
    async def _stream(self, ctx, streamer=None, *, stream_title=None):
        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else None

        if stream_title:
            stream_title = stream_title.strip()
            if "twitch.tv/" not in streamer:
                streamer = "https://www.twitch.tv/" + streamer
            if len(streamer) > 511:
                await ctx.send("The maximum length of the streamer url is 511 characters.")
                return
            if len(stream_title) > 128:
                await ctx.send("The maximum length of the stream title is 128 characters.")
                return
            activity = discord.Streaming(url=streamer, name=stream_title)
            await ctx.bot.change_presence(status=status, activity=activity)
        elif streamer is not None:
            await ctx.send_help()
            return
        else:
            await ctx.bot.change_presence(activity=None, status=status)
        await ctx.send("Done.")

async def setup(bot):
    await bot.add_cog(Core(bot))
