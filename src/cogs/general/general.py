import discord
from discord.ext import commands
from discord.utils import format_dt
import sys
import datetime
from src.core._help_command import EmbedConfig
from src.core.client import Client
from src.utils.user import get_status, get_roles_string
from src.utils.chat_formatting import humanize_timedelta

class General(commands.Cog):
    def __init__(self, bot: Client):
        self.bot = bot

    @commands.command(help="Display Bot's informations")
    async def info(self, ctx: commands.Context):
        owner = self.bot.get_owner()
        py_version = "[{}.{}.{}]({})".format(*sys.version_info[:3], "https://www.python.org/")
        dpy_version = "[{}]({})".format(discord.__version__, "https://github.com/Rapptz/discord.py")
        bot_name = self.bot.user.name
        since_created = format_dt(self.bot.user.created_at, 'R')
        created = format_dt(self.bot.user.created_at, 'f')
        created_field = f"{created} ({since_created})"

        data = discord.Embed(color=EmbedConfig.color)
        data.add_field(name="Bot's owner", value=owner.name)
        data.add_field(name="Python", value=py_version)
        data.add_field(name="discord.py", value=dpy_version)
        data.add_field(
            name=f"About {bot_name}",
            value=f"{bot_name} is bot created by {owner.mention}.",
            inline=False
        )
        data.add_field(
            name="Creation",
            value=created_field
        )

        await ctx.reply(embed=data)

    @commands.command()
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context):
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
            bot_name = self.bot.user.name,
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

        await ctx.reply(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, *, user: discord.Member = None):
        """Show informations about a member."""
        author = ctx.author
        server = ctx.guild
        if not user:
            user = author

        # Discord join & Server join
        joined_at = user.joined_at
        since_created = (ctx.message.created_at - user.created_at).days
        since_joined = (ctx.message.created_at - joined_at).days
        user_joined = format_dt(joined_at, 'D')
        user_created = format_dt(user.created_at, 'D')
        created_on = ("{}\n(il y a {} jours)").format(user_created, since_created)
        joined_on = ("{}\n(il y a {} jours)").format(user_joined, since_joined)
        # Voice
        voice_state = user.voice
        # Statut
        status_string, status_emoji = get_status(user)
        # roles
        role_string = get_roles_string(user)

        data = discord.Embed(description=status_string or '', color=user.color)
        data.set_author(name=status_emoji +
                            f" {' ~ '.join((str(user), user.display_name)) if user.display_name else str(user)}")
        data.set_thumbnail(url=user.avatar.url)
        if voice_state and voice_state.channel:
            data.add_field(name="Channel vocal",
                           value="{0.mention} ID: {0.id}".format(voice_state.channel),
                           inline=False)
        data.add_field(name="A rejoint Discord le", value=created_on)
        data.add_field(name="A rejoint ce serveur le", value=joined_on)
        if role_string: data.add_field(name="Rôle(s)", value=role_string, inline=False)
        data.set_footer(text=f"Member #{sorted(server.members, key=lambda m: m.joined_at).index(user)+1}")

        await ctx.reply(embed=data)

    @commands.command()
    async def avatar(self, ctx: commands.Context, user : discord.Member = None):
        if user == None:
            user = ctx.author

        if user.avatar.is_animated():
            url = str(user.avatar.replace(size=1024, format="gif"))
        else:
            url = str(user.avatar.replace(size=1024, static_format="png"))


        data = discord.Embed(title="**Avatar**", color=user.color)
        data.set_image(url=url)
        data.set_author(name=user, icon_url=url)

        await ctx.reply(embed=data)

async def setup(bot):
    await bot.add_cog(General(bot))