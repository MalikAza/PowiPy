import discord
from discord.ext import commands
from discord import app_commands
import os
from colorama import init, Fore
init()
from dotenv import load_dotenv
load_dotenv()
import logging

clear = lambda : os.system('clear') # cls for win
token = os.getenv('TOKEN')
invite_link = os.getenv('INVITE_LINK')
POWI_GUILD = discord.Object(id=os.getenv('POWI_GUILD_ID'))

# basics
intents = discord.Intents.all()
intents.message_content = True

class Client(commands.Bot):
    def __init__(self, command_prefix, intents, help_command):
        super().__init__(command_prefix=command_prefix, intents=intents, help_command=help_command)

    async def _get_loaded_cogs(self):
        return [str(cog).replace("cogs.", "") for cog in bot.extensions]
    
    def _get_unloaded_cogs(self, loaded):
        unloaded = []
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                if filename[:-3] not in loaded:
                    unloaded.append(filename[:-3])

        if not unloaded: return None
        return unloaded

    async def get_cogs(self):
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
        print('wow')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command.name)
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            await ctx.send(f"```py\n{error}\n```")

class CustomHelpCommand(commands.HelpCommand):

    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping): # [prefix]help
        print('bot help')
        print(mapping)
        return await super().send_bot_help(mapping)
    
    async def send_cog_help(self, cog): # [prefix]help Class_name_from_cog
        print('cog help')
        print(cog)
        return await super().send_cog_help(cog)
    
    async def send_group_help(self, group): # [prefix]help group_command
        print('group help')
        print(group)
        return await super().send_group_help(group)
    
    async def send_command_help(self, command): # [prefix]help command
        print('cmd help')
        print(command)
        return await super().send_command_help(command)

bot = Client(command_prefix=";", intents=intents, help_command=CustomHelpCommand())

# running
bot.run(token)