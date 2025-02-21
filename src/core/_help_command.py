from dataclasses import dataclass
from typing import Any, List, Mapping, Optional
from discord.ext import commands
import discord

@dataclass
class EmbedConfig:
    """Configuration class for Embed styling and formatting"""
    color: discord.Color = discord.Color(value=0xfee695) # Powi Color
    max_field_length: int = 1024
    max_command_help_length: int = 50
    empty_value: str = "ㅤ"

class CustomHelpCommand(commands.MinimalHelpCommand):

    def __init__(self):
        super().__init__()
        self.config = EmbedConfig()

    async def send(self, **kwargs):
        """Wrapper method for sending messages to the destination"""
        await self.get_destination().send(**kwargs)

    def create_base_embed(self, ctx: commands.Context) -> discord.Embed:
        """Creates a base embed with consistent styling"""
        return discord.Embed(
            color=self.config.color
        ).set_author(
            name=f"{ctx.me.name} Help Menu",
            icon_url=ctx.me.avatar.url
        ).set_footer(
            text=self._get_footer_text(ctx.prefix)
        )
    
    def _get_footer_text(self, prefix: str) -> str:
        """Generates consistent footer text"""
        return (
            f"Type {prefix}help <command> for more info on a command. "
            f"You can also type {prefix}help <category> for more info on a category."
        )
    
    def _get_command_signature_block(self, command: commands.Command) -> str:
        """Creates a formatted command signature block"""
        signature = f"Syntax: {self.get_command_signature(command)}"
        if command.aliases:
            signature += f"\nAliases: {','.join(command.aliases)}"
        return f"```{signature}```"
    
    def get_command_help_preview(self, command: commands.Command) -> str:
        """Gets a truncated preview of the command's help text"""
        if not command.help:
            return ''
        
        help_text = command.help.split('\n')[0]
        if len(help_text) > self.config.max_command_help_length:
            help_text = f"{help_text[:self.config.max_command_help_length]}..."
        return help_text
    
    def add_commands_to_field(
        self,
        embed: discord.Embed,
        title: str,
        commands: List[commands.Command],
        inline: bool = False
    ) -> None:
        """Adds commands to embed fields, splitting if necessary"""
        current_field = []
        current_length = 0

        for command in commands:
            command_help = self.get_command_help_preview(command)
            command_text = (
                f"**{command.name}** {command_help}\n"
                if command_help
                else f"**{command.name}**\n"
            )

            if current_length + len(command_text) > self.config.max_field_length:
                embed.add_field(
                    name=f"__{title}:__",
                    value=''.join(current_field),
                    inline=inline
                )
                current_field = []
                current_length = 0

            current_field.append(command_text)
            current_length += len(command_text)

        if current_field:
            embed.add_field(
                name=f"__{title}:__",
                value=''.join(current_field),
                inline=inline
            )
    
    async def send_bot_help(
        self,
        mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]],
        /
    ) -> None:
        ctx = self.context
        embed = self.create_base_embed(ctx)

        for cog, cog_commands in mapping.items():
            filtered_commands = await self.filter_commands(cog_commands, sort=True)
            if not filtered_commands:
                continue

            cog_name = getattr(cog, 'qualified_name', 'No Category')
            self.add_commands_to_field(embed, cog_name, filtered_commands)

        await self.send(embed=embed)

    async def send_command_help(self, command: commands.Command) -> None:
        embed = self.create_base_embed(self.context)
        embed.description = self._get_command_signature_block(command)
        embed.add_field(
            name=command.help or self.config.empty_value,
            value=self.config.empty_value
        )

        await self.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        embed = self.create_base_embed(self.context)
        cog_name = getattr(cog, 'qualified_name', 'No Category')

        if cog.description:
            embed.add_field(
                name=cog.description,
                value=self.config.empty_value,
                inline=False
            )

        cog_commands = await self.filter_commands(cog.get_commands(), sort=True)
        self.add_commands_to_field(embed, cog_name, cog_commands)

        await self.send(embed=embed)

    async def send_group_help(self, group: commands.Group) -> None:
        embed = self.create_base_embed(self.context)
        embed.description = self._get_command_signature_block(group)

        embed.add_field(
            name=group.help or self.config.empty_value,
            value=self.config.empty_value
        )

        group_commands = await self.filter_commands(group.commands, sort=True)
        self.add_commands_to_field(embed, "Subcommands", group_commands)
        
        await self.send(embed=embed)