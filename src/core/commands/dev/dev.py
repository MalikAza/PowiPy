from copy import copy
import discord
from src.core.client import Client
from discord.ext import commands

class Dev(commands.Cog):
    def __init__(self, bot: Client):
        self.bot = bot

    @commands.command(name='mock', aliases=['sudo'])
    @commands.is_owner()
    async def mock(self, ctx: commands.Context, user: discord.User, *, command: str):
        """
        Execute a command as if it was invoked by another user.

        The prefix must be not entered.
        """
        message = copy(ctx.message)
        message.author = user
        message.content = ctx.prefix + command

        self.bot.dispatch('message', message)