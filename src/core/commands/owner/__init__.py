from src.core.client import Client
from .owner import Owner

async def setup(bot: Client):
    await bot.add_cog(Owner(bot))