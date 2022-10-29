import discord
from discord.ext import commands
from discord import app_commands
import os
from colorama import init, Fore
init()
from dotenv import load_dotenv
load_dotenv()

clear = lambda : os.system('clear') # cls for win
token = os.getenv('TOKEN')
invite_link = os.getenv('INVITE_LINK')
POWI_GUILD = discord.Object(id=os.getenv('POWI_GUILD_ID'))

# basics
intents = discord.Intents.all()
intents.message_content = True

class Client(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=POWI_GUILD)
        await self.tree.sync(guild=POWI_GUILD)

bot = Client(command_prefix=";", intents=intents)

# console
@bot.event
async def on_ready():
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
    # loaded
    msg = "Extensions " + Fore.GREEN + "loaded" + Fore.RESET + ":\n"
    loaded = [str(cog).replace("cogs.", "") for cog in bot.extensions]
    msg += "{}".format(", ".join(sorted(loaded)))
    # unloaded
    msg += "\n\nExtensions " + Fore.RED + "not loaded" + Fore.RESET + ":\n"
    unloaded = []
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            if filename[:-3] not in loaded:
                unloaded.append(filename[:-3])
    if not unloaded:
        unloaded = ["None"]
    msg += "{}".format(", ".join(sorted(unloaded)))
    # invite link
    msg += '\n---------\n'
    msg += "Invite link:\n" + Fore.CYAN + invite_link + Fore.RESET
    print(msg)

# command errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send_help(ctx.command.name)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"```py\n{error}\n```")

# running
bot.run(token)