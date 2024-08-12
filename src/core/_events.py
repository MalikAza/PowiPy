import logging
import sys
import traceback
import os
from discord.ext import commands
from .client import Client

from rich import print
from rich.console import Console

console = Console()

def init_events(bot: Client):

    @bot.event
    async def on_ready():
        try:
            await _on_ready()
        except Exception as error:
            tb_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            print(
                "[bold red]Bot failed to be ready:[/bold red]\n\n" +
                tb_error
            )
            sys.exit(1)

    async def load_cogs():
        cogs_dir = os.path.join(os.path.dirname(__file__), '../cogs')
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py'):
                await bot.load_extension(f'src.cogs.{filename[:-3]}')

    async def _on_ready():
        os.system('clear') # cls for win

        logged_msg = f"Bot logged as [bold yellow]{bot.user}[/bold yellow]"
        separator = '-' * (len(logged_msg) - (len('[bold yellow]') + len('[/bold yellow]')))

        print(logged_msg, separator, sep='\n')

        await load_cogs()
        cogs = bot.get_cogs()

        loaded_msg = "Extensions [bold green]loaded[/bold green]:\n"
        loaded_msg += ", ".join(sorted(cogs['loaded']))

        unloaded_msg = "Extensions [bold red]not loaded[/bold red]:\n"
        unloaded_msg += ", ".join(sorted(cogs['unloaded']))

        print(loaded_msg, unloaded_msg, sep='\n\n')

        invite_link = os.getenv('INVITE_LINK')
        print(separator, f"Invite link:\n[cyan]{invite_link}[/cyan]", sep='\n', end='\n\n')

    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command.name)
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            tb_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

            bot._last_error = tb_error
            logging.getLogger('powipy').error(tb_error)

            await ctx.send(f"```Error in command '{ctx.command.name}'.\nPlease check console.```")