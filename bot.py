import discord
from discord.ext import commands
import os
import re
from colorama import init, Fore
init()
from dotenv import load_dotenv
load_dotenv()

clear = lambda : os.system('clear') # cls for win
token = os.getenv('TOKEN')
invite_link = os.getenv('INVITE_LINK')
POWI_GUILD = discord.Object(id=os.getenv('POWI_GUILD_ID'))
POWI_COLOR = 0xfee695

# basics
intents = discord.Intents.all()
intents.message_content = True

class Client(commands.Bot):
    def __init__(self, command_prefix, intents, help_command):
        super().__init__(command_prefix=command_prefix, intents=intents, help_command=help_command)

    async def _get_loaded_cogs(self):
        """
        This function returns a list of loaded cogs in a Python Discord bot.
        :return: The function `_get_loaded_cogs` is returning a list of strings, where each string
        represents the name of a loaded cog in the bot. The function is using a list comprehension to
        iterate over the `bot.extensions` attribute, which contains all the loaded extensions (cogs) in the
        bot, and then it is using the `replace` method to remove the "cogs." prefix from each
        """
        return [str(cog).replace("cogs.", "") for cog in bot.extensions]
    
    def _get_unloaded_cogs(self, loaded):
        """
        This function returns a list of unloaded Python files in the './cogs' directory based on a list of
        loaded files.
        
        :param loaded: A list of strings representing the names of the currently loaded cogs
        :return: a list of unloaded cog filenames (without the .py extension) from the ./cogs directory,
        based on the list of already loaded cog filenames passed as an argument. If there are no unloaded
        cogs, the function returns None.
        """
        unloaded = []
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                if filename[:-3] not in loaded:
                    unloaded.append(filename[:-3])

        if not unloaded: return None
        return unloaded

    async def get_cogs(self):
        """
        This function returns a tuple of loaded and unloaded cogs.
        :return: The function `get_cogs` returns a tuple containing two lists: `loaded` and `unloaded`. The
        `loaded` list contains the names of the currently loaded cogs, while the `unloaded` list contains
        the names of the cogs that are not currently loaded.
        """
        loaded = await self._get_loaded_cogs()
        unloaded = self._get_unloaded_cogs(loaded)

        return loaded, unloaded

    async def on_ready(self):
        clear()
        print("Bot logged as " + Fore.YELLOW + f"{bot.user}" + Fore.RESET + ".")
        print('---------')
        # loading core
        await bot.load_extension('core')
        # loading cogs
        try:
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    await bot.load_extension(f'cogs.{filename[:-3]}')
        except:
            pass
        # extensions un/loaded (console)
        loaded, unloaded = await self.get_cogs()
        # loaded
        msg = "Extensions " + Fore.GREEN + "loaded" + Fore.RESET + ":\n"
        msg += "{}".format(", ".join(sorted(loaded)))
        # unloaded
        msg += "\n\nExtensions " + Fore.RED + "not loaded" + Fore.RESET + ":\n"
        if not unloaded:
            unloaded = ["None"]
        msg += "{}".format(", ".join(sorted(unloaded)))
        # invite link
        msg += '\n---------\n'
        msg += "Invite link:\n" + Fore.CYAN + invite_link + Fore.RESET
        print(msg)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command.name)
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            await ctx.send(f"```py\n{error}\n```")

class CustomHelpCommand(commands.MinimalHelpCommand):

    def __init__(self):
        super().__init__()

### Utilies method ###
    async def send(self, **kwargs):
        await self.get_destination().send(**kwargs)

    def base_embed(self, ctx):
        embed = discord.Embed(color=discord.Color(value=POWI_COLOR))
        embed.set_author(name=f"{ctx.me.name} Help Menu", icon_url=ctx.me.avatar.url)
        embed.set_footer(text=f"Type {ctx.prefix}help <command> for more info on a command. " + 
                                f"You can also type {ctx.prefix}help <category> for more info on a category.")
        
        return embed
    
    def help_embed_field(self, ctx, embed, title, commands, args = True):
        embed.add_field(name=f"__{title}:__",
                        value="\n".join(["**" + re.sub(r'\[.*?\]', '', cmd_sign) + f"** {cmd_help}"
                                        if 'help' not in cmd_sign else f"**{ctx.prefix}help** {cmd_help}"
                                        for cmd_sign, cmd_help in commands]),
                        inline=False)
        
    def help_embed_description(self, embed, command):
        embed.description = (f"```Syntax: {self.get_command_signature(command)}" + 
                            ((f"\nAlias: " + ', '.join(command.aliases)) if command.aliases else '') +
                            '```')
        embed.add_field(name=command.help, value="ㅤ")
    
    async def get_cmd_list(self, commands):
        if filtered_cmds := await self.filter_commands(commands, sort=True):
            cmds = []
            for cmd in filtered_cmds:
                cmds.append((self.get_command_signature(cmd), cmd.help))

            return cmds
        return False
######

    async def send_error_message(self, error): return

    # [prefix]help
    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = self.base_embed(ctx)

        for cog, commands in mapping.items():
            if cmd_list := await self.get_cmd_list(commands):
                cog_name = getattr(cog, "qualified_name", "No Category")
                self.help_embed_field(ctx, embed, cog_name, cmd_list)

        await self.send(embed=embed)
    
    # [prefix]help command
    async def send_command_help(self, command):
        ctx = self.context
        embed = self.base_embed(ctx)
        self.help_embed_description(embed, command)

        await self.send(embed=embed)

    # [prefix]help Class_name_from_cog
    async def send_cog_help(self, cog):
        ctx = self.context
        embed = self.base_embed(ctx)
        cog_name = getattr(cog, "qualified_name", "No Category")

        if cog.description: embed.add_field(name=cog.description, value="ㅤ", inline=False)
        self.help_embed_field(ctx, embed, cog_name, await self.get_cmd_list(cog.get_commands()))

        await self.send(embed=embed)
    
    # [prefix]help group_command
    async def send_group_help(self, group):
        ctx = self.context
        embed = self.base_embed(ctx)
        self.help_embed_description(embed, group)
        self.help_embed_field(ctx, embed, "Subcommands", await self.get_cmd_list(group.commands), False)

        await self.send(embed=embed)

bot = Client(command_prefix=";",
             intents=intents,
             help_command=CustomHelpCommand())

# running
bot.run(token,
        log_handler=None) # disabling logging