import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Optional, Union
from random import choice
import os
from discord.ui import Button

from src.core.client import Client

POWI_GUILD = discord.Object(id=os.getenv('GUILD_ID'))
RPS_EMOJIS = ['Rock', 'Paper', 'Scissors']
GREY_BTN = discord.ButtonStyle.grey
GREEN_BTN = discord.ButtonStyle.green
RED_BTN = discord.ButtonStyle.red
BLUE_BTN = discord.ButtonStyle.blurple

class RockPaperScissors(discord.ui.View):
    base_interaction: discord.Interaction
    children: List[Button]

    def __init__(self, author: Union[discord.User, discord.Member], bot_user: discord.ClientUser):
        super().__init__()
        self.author = author
        self.bot_user = bot_user

    async def button_result(self, button_label):
        chosen = choice(RPS_EMOJIS)

        if button_label == chosen:
            winner = "Tie! No one win."
            colors = [GREY_BTN]*3
        else:
            if button_label == 'Rock':
                if chosen == 'Paper':
                    winner = self.bot_user.mention
                    colors = [RED_BTN, BLUE_BTN, GREY_BTN]
                else:
                    winner = self.author.mention
                    colors = [GREEN_BTN, GREY_BTN, BLUE_BTN]
            elif button_label == 'Paper':
                if chosen == 'Rock':
                    winner = self.author.mention
                    colors = [BLUE_BTN, GREEN_BTN, GREY_BTN]
                else:
                    winner = self.bot_user.mention
                    colors = [GREY_BTN, RED_BTN, BLUE_BTN]
            elif button_label == 'Scissors':
                if chosen == 'Rock':
                    winner = self.bot_user.mention
                    colors = [BLUE_BTN, GREY_BTN, RED_BTN]
                else:
                    winner = self.author.mention
                    colors = [GREY_BTN, BLUE_BTN, GREEN_BTN]

        for i in range(0,3):
            self.children[i].disabled = True
            self.children[i].style = colors[i]

        data = discord.Embed(title="Rock, Paper, Scissors", description=f"**{self.author.display_name}**'s game.",
        color=(
            discord.Colour.green() if GREEN_BTN in colors
            else discord.Colour.red() if RED_BTN in colors
            else discord.Colour.og_blurple()))
        data.add_field(name="Winner", value=winner)

        await self.base_interaction.edit_original_response(embed=data, view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.base_interaction.edit_original_response(view=self)

    @discord.ui.button(label='Rock', style=GREY_BTN, emoji='🪨')
    async def rock(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id == self.author.id:
            await self.button_result(button.label)
            await interaction.response.defer()
            self.stop()
        else:
            await interaction.response.send_message(
                f"It's not your game D: ! It's {self.author.mention}'s one.",
                ephemeral=True)

    @discord.ui.button(label='Paper', style=GREY_BTN, emoji='📄')
    async def paper(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id == self.author.id:
            await self.button_result(button.label)
            await interaction.response.defer()
            self.stop()
        else:
            await interaction.response.send_message(
                f"It's not your game D: ! It's {self.author.mention}'s one.",
                ephemeral=True)

    @discord.ui.button(label='Scissors', style=GREY_BTN, emoji='✂️')
    async def scissors(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id == self.author.id:
            await self.button_result(button.label)
            await interaction.response.defer()
            self.stop()
        else:
            await interaction.response.send_message(
                f"It's not your game D: ! It's {self.author.mention}'s one.",
                ephemeral=True)

class SlashCommands(commands.Cog):
    def __init__(self, bot: Client) -> None:
        self.bot = bot

### ZUnivers related ###
    @app_commands.command(name="ding")
    @app_commands.guilds(POWI_GUILD)
    async def ding(self, interaction: discord.Interaction) -> None:
        """Pour mieux !journa."""
        await interaction.response.send_message("<#808432657838768168> Ding ! ```!journa```", ephemeral=True)

    @app_commands.command(name="midi")
    @app_commands.guilds(POWI_GUILD)
    async def midi(self, interaction: discord.Interaction) -> None:
        """Wall-it l'ascension."""
        await interaction.response.send_message("<#824253593892290561> Wall-it! ```!as```", ephemeral=True)

######

    @app_commands.command(name="ban")
    @app_commands.guilds(POWI_GUILD)
    @app_commands.describe(
        user = "The user you want to fake-ban.",
        reason = "The reason for the fake-ban."
    )
    async def ban(self, interaction: discord.Interaction, user: discord.User, *, reason: Optional[str] = None) -> None:
        """Fake-ban a user."""
        if user.bot:
            user = interaction.user
            reason = "no u"
        msg = f"{user.mention} has been banned."
        if reason != None: msg += f"\n**Reason:** `{reason}`"
        await interaction.response.send_message(msg)

    @app_commands.command(name="invite")
    @app_commands.guilds(POWI_GUILD)
    @app_commands.describe(user='The user you want to tag, to show server link.')
    async def invite(self, interaction: discord.Interaction, user: Optional[discord.User] = None) -> None:
        """Show the server link."""
        msg = ""
        if user: msg += f"{user.mention} : "
        msg += os.getenv('DISCORD_INVITE')
        await interaction.response.send_message(msg)

    @app_commands.command(name="rps")
    @app_commands.guilds(POWI_GUILD)
    async def rps(self, interaction: discord.Interaction) -> None:
        """Rock, Paper, Scissors game."""
        author = interaction.user
        bot_user = interaction.client.user
        view = RockPaperScissors(author, bot_user)
        data = discord.Embed(title="Rock, Paper, Scissors", description=f"**{author.display_name}**'s game.", color=discord.Colour.og_blurple())
        view.base_interaction = interaction
        await interaction.response.send_message(embed=data, view=view)
        await view.wait()

    @app_commands.command(name="ff")
    @app_commands.guilds(POWI_GUILD)
    async def ff(self, interaction: discord.Interaction) -> None:
        """To forfeit."""
        author = interaction.user

        await interaction.response.send_message(f"""{author.mention} *has disconnected...*""")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SlashCommands(bot))