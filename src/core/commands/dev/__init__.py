from src.core.client import Client
from .dev import Dev

async def setup(bot: Client):
    await bot.add_cog(Dev(bot))