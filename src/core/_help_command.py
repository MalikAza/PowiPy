import re
from typing import Any, List, Mapping, Optional, Tuple
from discord.ext import commands
import discord

class CustomHelpCommand(commands.MinimalHelpCommand):

    def __init__(self):
        super().__init__()
        self.POWI_COLOR = 0xfee695

### Utilies method ###
    async def send(self, **kwargs):
        await self.get_destination().send(**kwargs)

    def base_embed(self, ctx: commands.Context) -> discord.Embed:
        embed = discord.Embed(color=discord.Color(value=self.POWI_COLOR))
        embed.set_author(name=f"{ctx.me.name} Help Menu", icon_url=ctx.me.avatar.url)
        embed.set_footer(text=f"Type {ctx.prefix}help <command> for more info on a command. " + 
                                f"You can also type {ctx.prefix}help <category> for more info on a category.")
        
        return embed

    def split_embed_fields(
        self,
        ctx: commands.Context,
        embed: discord.Embed,
        title: str,
        commands: List[Tuple[str, str | None]],
        args: Optional[bool] = True
    ) -> None:
        MAX_FIELD_LENGTH = 1024
        description = ''

        for cmd_name, cmd_desc in commands:
            cmd_text = f'**{cmd_name}**: {cmd_desc}\n' if cmd_desc else f'**{cmd_name}**\n'

            if len(description) + len(cmd_text) > MAX_FIELD_LENGTH:
                embed.add_field(name=title, value=description, inline=False)
                description = ''

            description += cmd_text

        if description:
            embed.add_field(name=title, value=description, inline=False)
        
    def help_embed_description(self, embed: discord.Embed, command: commands.Command):
        embed.description = (f"```Syntax: {self.get_command_signature(command)}" + 
                            ((f"\nAlias: " + ', '.join(command.aliases)) if command.aliases else '') +
                            '```')
        embed.add_field(name='Description', value=command.help or "ㅤ")
    
    async def get_cmd_list(self, commands: List[commands.Command[Any, ..., Any]]):
        if filtered_cmds := await self.filter_commands(commands, sort=True):
            cmds: List[Tuple[str, str | None]] = []
            for cmd in filtered_cmds:
                cmds.append((self.get_command_signature(cmd), cmd.help))

            return cmds
        
        return False
######

    async def send_error_message(self, error): return

    # [prefix]help
    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]], /):
        ctx = self.context
        embed = self.base_embed(ctx)

        for cog, commands in mapping.items():
            if cmd_list := await self.get_cmd_list(commands):
                cog_name = getattr(cog, "qualified_name", "No Category")
                self.split_embed_fields(ctx, embed, cog_name, cmd_list)

        await self.send(embed=embed)
    
    # [prefix]help command
    async def send_command_help(self, command: commands.Command):
        ctx = self.context
        embed = self.base_embed(ctx)
        self.help_embed_description(embed, command)

        await self.send(embed=embed)

    # [prefix]help Class_name_from_cog
    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.context
        embed = self.base_embed(ctx)
        cog_name = getattr(cog, "qualified_name", "No Category")

        if cog.description: embed.add_field(name=cog.description, value="ㅤ", inline=False)
        self.split_embed_fields(ctx, embed, cog_name, await self.get_cmd_list(cog.get_commands()))

        await self.send(embed=embed)
    
    # [prefix]help group_command
    async def send_group_help(self, group: commands.Group):
        ctx = self.context
        embed = self.base_embed(ctx)
        self.help_embed_description(embed, group)
        self.split_embed_fields(ctx, embed, "Subcommands", await self.get_cmd_list(group.commands), False)

        await self.send(embed=embed)