from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import shutil
from typing import Any, Dict

class BaseStorage(ABC):
    """Abstract base class defining storage interface"""

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """Must implement method to retrieve data"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Must implement method to store data"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Must implement method to delete data"""
        pass

class JSONStorage(BaseStorage):
    """JSON file storage implementation"""
    _data: Dict[str, Any]
    storage_name: str

    def __init__(self, storage_name: str):
        self.logger = logging.getLogger(f'{storage_name}Storage')
        self.storage_name = storage_name
        self._data = {}
        self._lock = asyncio.Lock()

        # Get project root directory
        self.project_root = Path(__file__).parent.parent.parent

        # Set up storage paths
        self.storage_dir = self.project_root / 'data'
        self.backup_dir = self.storage_dir / 'backup'
        self.file_path = self.storage_dir / f'{storage_name.lower()}.json'

        # Create directories if they don't exists
        self.storage_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        # Load initial data
        self._ensure_file_exists()
        self._load_data()

    def _save_data(self, data: Dict[str,  Any]) -> None:
        """Save data to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except Exception as error:
            self.logger.error(f"Error saving data: {error}")

    def _create_backup(self) -> None:
        """Create a backup for the current data file"""
        if self.file_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'{self.storage_name.lower()}_{timestamp}.json'
            try:
                shutil.copy2(self.file_path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            except Exception as error:
                self.logger.error(f"Error creating backup: {error}")

    def _ensure_file_exists(self) -> None:
        """Ensure the JSON file exists with valid initial data"""
        if not self.file_path.exists():
            self._save_data({})

    def _load_data(self) -> None:
        """Load data from JSON file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self._data = json.load(file)
        except json.JSONDecodeError:
            self.logger.error(f"Corrupted JSON file: {self.file_path}")
            self._create_backup()
            self._data = {}
            self._save_data(self._data)
        except Exception as error:
            self.logger.error(f"Error loading data: {error}")
            self._data = {}

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from storage"""
        async with self._lock:
            return self._data.get(key, default)
        
    async def set(self, key: str, value: Any) -> None:
        """Set value in storage"""
        async with self._lock:
            self._data[key] = value
            self._save_data(self._data)

    async def delete(self, key: str) -> bool:
        """Delete value from storage"""
        async with self._lock:
            if key in self._data:
                del self._data[key]
                self._save_data(self._data)
                return True
            return False
        
    async def clear(self) -> None:
        """Clear all data from storage"""
        async with self._lock:
            self._create_backup()
            self._data = {}
            self._save_data(self._data)

    async def get_all(self) -> Dict[str, Any]:
        """Get all stored data"""
        async with self._lock:
            return self._data.copy()
        
class GuildStorage(JSONStorage):
    """Specialized storage for guild-specific data"""

    async def get_guild_data(self, guild_id: int) -> Dict[str, Any]:
        """Get all data for specific guild"""
        async with self._lock:
            return self._data.get(str(guild_id), {})
        
    async def set_guild_data(self, guild_id: int, key: str, value: Any) -> None:
        """Set data for specific guild"""
        async with self._lock:
            guild_data = self._data.get(str(guild_id), {})
            guild_data[key] = value
            self._data[str(guild_id)] = guild_data
            self._save_data(self._data)

    async def delete_guild_data(self, guild_id: int) -> None:
        """Delete all data for specific guild"""
        async with self._lock:
            if str(guild_id) in self._data:
                del self._data[str(guild_id)]
                self._save_data(self._data)