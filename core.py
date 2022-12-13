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

from .cogs.utils.chat_formatting import humanize_timedelta

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
        # loaded
        loaded = [str(cog).replace("cogs.", "") for cog in self.bot.extensions]
        # unloaded
        unloaded = []
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                if filename[:-3] not in loaded:
                    unloaded.append(filename[:-3])
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

    @commands.command(aliases=['powinfo'], help="Display Bot's informations")
    async def info(self, ctx):
        owner = self.bot.get_user(os.getenv('OWNER_ID'))
        hitsu = self.bot.get_user(os.getenv('HITSU_ID'))
        wyrd = self.bot.get_user(os.getenv('WYRD_ID'))
        bot_user = self.bot.get_user(os.getenv('USER_BOT_ID'))
        py_version = "[{}.{}.{}]({})".format(*sys.version_info[:3], "https://www.python.org/")
        dpy_version = "[{}]({})".format(discord.__version__, "https://github.com/Rapptz/discord.py")
        bot_name = self.bot.user.name
        since_created = (ctx.message.created_at - self.bot.user.created_at).days
        created = self.bot.user.created_at.strftime("%d %b %Y %H:%M")
        footer = f"{created} ({since_created} days ago)"


        data = discord.Embed(color=discord.Colour(0xE9D286))
        data.add_field(name="Bot's owner", value=f"{owner.name}#{owner.discriminator}")
        data.add_field(name="Python", value=py_version)
        data.add_field(name="discord.py", value=dpy_version)
        data.add_field(name=f"About {bot_name}",
                       value=f"{bot_name} is bot created by {owner.mention} with the help of "
                             f"{hitsu.mention} & {wyrd.mention}.", inline=False)
        data.set_footer(text=footer, icon_url=self.bot.user.avatar)

        await ctx.send(embed=data)

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

    @commands.command()
    async def serverinfo(self, ctx):
        """Show server informations."""
        server = ctx.guild
        created_at = "Créé le {date_and_time}. C'étais {relative_time} !".format(
            date_and_time=discord.utils.format_dt(server.created_at),
            relative_time=discord.utils.format_dt(server.created_at, "R")
        )
        online = len([m.status for m in server.members if m.status != discord.Status.offline])
        total_users = server.member_count
        member_msg = f"Utilisateurs en ligne: **{online}/{total_users}**\n"

        text_channels = len(server.text_channels)
        voice_channels = len(server.voice_channels)
        
        online_stats = {
            "Humains : ": lambda x: not x.bot,
            "\nBots : ": lambda x: x.bot,
            "\N{LARGE GREEN CIRCLE}": lambda x: x.status is discord.Status.online,
            "\N{LARGE ORANGE CIRCLE}": lambda x: x.status is discord.Status.idle,
            "\N{LARGE RED CIRCLE}": lambda x: x.status is discord.Status.do_not_disturb,
            "\N{MEDIUM WHITE CIRCLE}\N{VARIATION SELECTOR-16}": lambda x: x.status is discord.Status.offline,
            "\N{LARGE PURPLE CIRCLE}": lambda x: any(a.type is discord.ActivityType.streaming for a in x.activities),
            "\N{MOBILE PHONE}": lambda x: x.is_on_mobile()
        }
        count = 1
        for emoji, value in online_stats.items():
            try:
                num = len([m for m in server.members if value(m)])
            except Exception as error:
                print(error)
                continue
            else:
                member_msg += f"{emoji} **{num}** " + ("\n" if count%2 == 0 else "")
            count += 1

        verif = {
            "none": "0 - Aucune",
            "low": "1 - Faible",
            "medium": "2 - Moyenne",
            "high": "3 - Haute",
            "hightest": "4 - La plus haute"
        }

        joined_on = "{bot_name} a rejoint ce serveur le {bot_join}. Il y a plus de {since_join} jours !".format(
            bot_name = ctx.bot.user.name,
            bot_join = server.me.joined_at.strftime("%d %b %Y %H:%M:%S"),
            since_join = (ctx.message.created_at - server.me.joined_at).days
        )

        embed = discord.Embed(description=(f"{server.description}\n\n" if server.description else "") + created_at,
                color=server.me.color)

        embed.set_author(name=server.name,
        icon_url="https://cdn.discordapp.com/emojis/457879292152381443.png" if "VERIFIED" in server.features
        else "https://cdn.discordapp.com/emojis/508929941610430464.png" if "PARTNERED" in server.features
        else None)

        if server.icon:
            embed.set_thumbnail(url=server.icon)

        embed.add_field(name="Membres :", value=member_msg)

        embed.add_field(name="Salons :",
                        value="\N{SPEECH BALLOON} Text : {text}\n"
                        "\N{SPEAKER WITH THREE SOUND WAVES} Vocal : {voice}\n"
                            .format(text=f"**{text_channels}**",
                                    voice=f"**{voice_channels}**"))

        embed.add_field(name="Utilitaire :",
                        value="Propriétaire : {owner}\nNiveau verif. : {verif}\nServer ID : {id}"
                            .format(owner=f"**{server.owner}**",
                                    verif=f"**{verif[str(server.verification_level)]}**",
                                    id=f"**{server.id}**"),
                        inline=False)

        embed.add_field(name="Divers :",
                        value="Salon AFK : {afk_chan}\nPériode d'inactivité : {afk_timeout}\nEmojis : {emoji_count}\nRôles : {role_count}"
                        .format(
                            afk_chan=f"**{str(server.afk_channel) if server.afk_channel else 'Aucun'}**",
                            afk_timeout=f"**{humanize_timedelta(timedelta=datetime.timedelta(seconds=server.afk_timeout))}**",
                            emoji_count=f"**{len(server.emojis)}**",
                            role_count=f"**{len(server.roles)}**"
                        ),
                        inline=False)

        if server.splash:
            embed.set_image(url=server.splash.replace(format="png"))
        
        embed.set_footer(text=joined_on)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Core(bot))
