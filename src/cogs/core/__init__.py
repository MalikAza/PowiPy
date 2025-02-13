from src.core.client import Client
from .core import Core

async def setup(bot: Client):
    await bot.add_cog(Core(bot))