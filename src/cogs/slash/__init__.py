from src.core.client import Client
from .slash import SlashCommands

async def setup(bot: Client):
    await bot.add_cog(SlashCommands(bot))