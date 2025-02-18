import logging
import os
from typing import List, TypedDict
import discord
from discord.ext import commands

from src.core._cog_loader import CogLoader
from src.utils.logger import init_logging
from ._help_command import CustomHelpCommand

class LoadedAndUnloadedCogs(TypedDict):
    loaded: List[str]
    unloaded: List[str]

class Client(commands.Bot):
    _last_error: str

    def __init__(self, command_prefix: str):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(command_prefix=command_prefix, intents=intents, help_command=CustomHelpCommand())

        init_logging('powipy', log_level=logging.INFO, file_log_level=logging.WARNING)
        self._init_events()

    async def setup_hook(self):
        await super().setup_hook()

        from ._events import OnAppCommandErrorHandler
        OnAppCommandErrorHandler.set_bot(self)

        self.tree.error(OnAppCommandErrorHandler.on_app_command_error)
    
    def _init_events(self):
        from ._events import init_events
        init_events(self)

    def _get_loaded_cogs(self) -> List[str]:
        """
        Retrieve a list of names of loaded cogs in the bot.
        """
        return [str(cog).replace("src.", "").replace("cogs.", "") for cog in self.extensions]
    
    def _get_unloaded_cogs(self, loaded: List[str]) -> List[str]:
        """
        Retrieve a list of unloaded cog filenames (without the .py extension) from the ./cogs directory.
        """
        potential_cogs = CogLoader(self).get_potential_packages()

        return [cog for cog in potential_cogs if cog not in loaded]

    def get_cogs(self) -> LoadedAndUnloadedCogs:
        """
        Retrieve a dictionary containing the loaded and unloaded cogs names.
        """
        loaded = self._get_loaded_cogs()
        unloaded = self._get_unloaded_cogs(loaded)
        
        return {
            'loaded': loaded,
            'unloaded': unloaded
        }
    
    def get_invite_link(self) -> str:
        client_id = os.getenv('CLIENT_ID')

        return f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions=0&scope=bot%20applications.commands"
    
    def get_main_guild(self) -> discord.Guild:
        return discord.Object(id=os.getenv('GUILD_ID'))

    async def login(self, token: str) -> None:
        logging.getLogger('powipy').info('Connecting to Discord...')
        return await super().login(token)