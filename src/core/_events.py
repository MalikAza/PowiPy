import logging
import sys
import traceback
import os
import discord
from discord.ext import commands

from src.core._cog_loader import CogLoader
from src.core._help_command import CustomHelpCommand, EmbedConfig
from src.utils.commands import find_similar_commands
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

    async def _on_ready():
        os.system('clear') # cls for win

        logged_msg = f"Bot logged as [bold yellow]{bot.user}[/bold yellow]"
        separator = '-' * (len(logged_msg) - (len('[bold yellow]') + len('[/bold yellow]')))

        print(logged_msg, separator, sep='\n')

        await CogLoader(bot).init()
        cogs = bot.get_cogs()

        loaded_msg = "Extensions [bold green]loaded[/bold green]:\n"
        loaded_msg += ", ".join(sorted(cogs['loaded']))

        unloaded_msg = "Extensions [bold red]not loaded[/bold red]:\n"
        unloaded_msg += ", ".join(sorted(cogs['unloaded']))

        print(loaded_msg, unloaded_msg, sep='\n\n')

        invite_link = bot.get_invite_link()
        print(separator, f"Invite link:\n[cyan]{invite_link}[/cyan]", sep='\n', end='\n\n')

    @bot.event
    async def on_command(ctx: commands.Context):
        """Handle empty group command invocations"""
        if isinstance(ctx.command, commands.Group) and not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception):
        error = getattr(error, 'original', error)

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command)

        elif isinstance(error, commands.CommandNotFound):
            message_content = ctx.message.content.strip()
            attempted_command = message_content[len(ctx.prefix):].split()[0]

            available_commands = [cmd for cmd in bot.commands]
            similar_commands = find_similar_commands(attempted_command, available_commands)

            if similar_commands:
                suggestion = similar_commands[0]
                embed = discord.Embed(
                    color=EmbedConfig().color,
                    title="Did you mean...?",
                    description=f"**{ctx.prefix}{suggestion.name}** {CustomHelpCommand().get_command_help_preview(suggestion)}"
                )
                await ctx.reply(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            perms_list = '\n'.join(f"- {perm}" for perm in missing_perms)

            await ctx.reply(f"You need the following permissions:\n{perms_list}")
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(f"Invalid argument: {str(error)}")
        else:
            tb_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

            bot._last_error = tb_error
            bot._logger.error(tb_error)

            await ctx.reply(f"```Error in command '{ctx.command.name}'.\nPlease check console.```")

class OnAppCommandErrorHandler:
    bot: Client | None = None

    @classmethod
    def set_bot(cls, bot: Client):
        cls.bot = bot

    @classmethod
    async def on_app_command_error(
        cls,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ) -> None:
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"This command is on cooldown! Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
            return
            
        elif isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(
                f"You don't have the required permissions to use this command! "
                f"Required permissions: {', '.join(error.missing_permissions)}",
                ephemeral=True
            )
            return
            
        elif isinstance(error, discord.app_commands.MissingRole):
            await interaction.response.send_message(
                f"You're missing the required role to use this command!",
                ephemeral=True
            )
            return
            
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                f"I don't have the required permissions to execute this command! "
                f"Required permissions: {', '.join(error.missing_permissions)}",
                ephemeral=True
            )
            return
            
        elif isinstance(error, discord.app_commands.CommandNotFound):
            await interaction.response.send_message(
                "This command doesn't exist!",
                ephemeral=True
            )
            return
            
        else:
            tb_error = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

            OnAppCommandErrorHandler.bot._last_error = tb_error
            cls.bot._logger.error(tb_error)
            
            await interaction.response.send_message(
                "An unexpected error occurred!",
                ephemeral=True
            )