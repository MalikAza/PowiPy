import logging
import os
from typing import List, Optional, Sequence, TypedDict, Union
import discord
from discord.ext import commands

from src.core._cog_loader import CogLoader
from src.utils.logger import init_logging
from ._help_command import CustomHelpCommand

class LoadedAndUnloadedCogs(TypedDict):
    loaded: List[str]
    unloaded: List[str]

class Client(commands.Bot):
    _last_error: str = None
    id: int

    def __init__(self, command_prefix: str):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            help_command=CustomHelpCommand()
        )

        self._logger = init_logging('powipy', log_level=logging.INFO, file_log_level=logging.WARNING)
        from ._events import get_ready
        get_ready(self)

    async def setup_hook(self):
        await super().setup_hook()

        from ._events import setup_events
        setup_events(self)

        from ._events import OnAppCommandErrorHandler
        OnAppCommandErrorHandler.set_bot(self)
        self.tree.error(OnAppCommandErrorHandler.on_app_command_error)

    def _get_loaded_cogs(self) -> List[str]:
        """
        Retrieve a list of names of loaded cogs in the bot.
        """
        return [
            ext_name.replace(CogLoader.base_cog_import_path, "")
            for ext_name in self.extensions.keys()
            if not ext_name.startswith(CogLoader.core_cog_import_path)
        ]
    
    def _get_unloaded_cogs(self) -> List[str]:
        """
        Retrieve a list of unloaded cog filenames (without the .py extension) from the ./cogs directory.
        """
        potential_cogs = set(CogLoader(self).get_potential_packages())
        loaded = set(self._get_loaded_cogs())

        return sorted(list(potential_cogs - loaded), key=str.lower)

    def get_cogs(self) -> LoadedAndUnloadedCogs:
        """
        Retrieve a dictionary containing the loaded and unloaded cogs names.
        """
        loaded = self._get_loaded_cogs()
        unloaded = self._get_unloaded_cogs()
        
        return {
            'loaded': loaded,
            'unloaded': unloaded
        }
    
    def get_invite_link(self) -> str:
        return f"https://discord.com/api/oauth2/authorize?client_id={self.id}&permissions=0&scope=bot%20applications.commands"
    
    def get_main_guild(self) -> discord.Guild:
        return discord.Object(id=os.getenv('GUILD_ID'))

    async def login(self, token: str) -> None:
        self._logger.info('Connecting to Discord...')
        return await super().login(token)
    
    def get_owner(self) -> discord.User:
        return self.get_user(self.owner_id)
    
    async def send_to_owner(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: discord.Embed = ...,
        file: discord.File = ...,
        stickers: Sequence[Union[discord.GuildSticker, discord.StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: discord.AllowedMentions = ...,
        reference: Union[discord.Message, discord.MessageReference, discord.PartialMessage] = ...,
        mention_author: bool = ...,
        view: discord.ui.View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> discord.Message:
        args = {key: value for key, value in locals().items() if key != 'self'}
        
        owner = self.get_owner()
        return await owner.send(**args)