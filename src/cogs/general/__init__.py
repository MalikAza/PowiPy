from src.core.client import Client
from .general import General

async def setup(bot: Client):
    await bot.add_cog(General(bot))