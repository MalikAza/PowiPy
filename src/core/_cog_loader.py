import importlib
import importlib.util
import logging
import os
from typing import List

from discord.ext import commands
from src.utils.logger import init_logging

class CogLoadError(Exception):
    pass

class CogLoader:
    __cogs_dir = os.path.join(os.path.dirname(__file__), '../cogs')
    base_cog_import_path = 'src.cogs.'

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_logging('CogLoader', log_level=logging.INFO, file_log_level=logging.WARNING)
        self.logger = logging.getLogger('CogLoader')

    def __check_directory(self):
        if not os.path.exists(self.__cogs_dir):
            raise CogLoadError(f"Cogs directory not found: {self.__cogs_dir}")
        
    def get_potential_packages(self) -> List[str]:
        try:
            return [
                directory for directory in os.listdir(self.__cogs_dir)
                if os.path.isdir(os.path.join(self.__cogs_dir, directory))
                and directory != '__pycache__'
                and not directory.startswith('.')
            ]
        except Exception as e:
            raise CogLoadError(f"Error reading cogs directory: {str(e)}")

    async def __verify_cog_structure(self, cog_path: str) -> bool:
        try:
            init_path = os.path.join(cog_path, '__init__.py')
            if not os.path.exists(init_path):
                self.logger.warning(f"Missing __init__.py in {cog_path}")
                return False
            
            package_name = os.path.basename(cog_path)

            try:
                module = importlib.import_module(f"{self.base_cog_import_path}{package_name}")

                if not hasattr(module, 'setup'):
                    self.logger.warning(f"No setup function found in {cog_path}")
                    return False
                
                return True
            
            except ImportError as e:
                self.logger.warning(f"Could not import cog package {package_name}: {str(e)}")
                return False
        
        except Exception as e:
            self.logger.warning(f"Error verifying cog structure for {cog_path}: {str(e)}")
            return False

    async def __load_cog(self, cog_package: str):
        cog_path = os.path.join(self.__cogs_dir, cog_package)
        cog_import_path = f'{self.base_cog_import_path}{cog_package}'

        try:
            if not await self.__verify_cog_structure(cog_path):
                self.logger.warning(f"Skipping {cog_package} due to invalid structure")
                return

            await self.bot.load_extension(cog_import_path)

        except Exception as e:
            self.logger.error(f"Failed to load cog {cog_package}: {str(e)}", exc_info=True)

    async def init(self):
        self.__check_directory()

        cog_packages = self.get_potential_packages()

        for cog_package in cog_packages:
            await self.__load_cog(cog_package)