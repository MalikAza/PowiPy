import asyncio
from typing import Any, Callable, Coroutine, List, Optional, Protocol, Tuple, Union
import discord
from discord.ext import commands

from src.core.client import Client

class ReactionContext(Protocol):
    """Protocol defining the minimum context needed for reaction checking."""

    @property
    def bot(self) -> Client:
        ...

def create_reaction_check(
    message_id: int,
    user_id: Optional[int],
    emoji_list: List[str]
) -> Callable[[discord.Reaction, Union[discord.User, discord.Member]], bool]:
    """
    Create a check function for reaction_add event.
    
    Args:
        message_id: The ID of the message to check reactions on
        user_id: The ID of the user whose reactions to check (None for any user)
        emoji_list: List of emoji strings that are valid reactions
        
    Returns:
        A function that can be used as a check for bot.wait_for('reaction_add')
    """
    def check(reaction: discord.Reaction, user: Union[discord.User, discord.Member]) -> bool:
        is_valid_user = True if user_id is None else user.id == user_id
        return (
            is_valid_user and
            reaction.message.id == message_id and
            str(reaction.emoji) in emoji_list
        )
    return check

async def wait_for_reaction(
    bot: Client,
    message: discord.Message,
    user: Optional[Union[discord.User, discord.Member]],
    emoji_list: List[str],
    timeout: float = 30.0
) -> Tuple[Optional[discord.Reaction], Optional[Union[discord.User, discord.Member]]]:
    """
    Wait for a specific user (or any user) to react to a message with one of the specified emojis.
    
    Args:
        bot: The bot instance to use for waiting
        message: The message to wait for reactions on
        user: The user whose reactions to check (None for any user)
        emoji_list: List of emojis that are considered valid
        timeout: How long to wait before timing out (in seconds)
        
    Returns:
        A tuple of (reaction, user) if successful, or (None, None) if timed out
    """
    user_id = user.id if user is not None else None
    check = create_reaction_check(message.id, user_id, emoji_list)

    try:
        reaction, reaction_user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
        return reaction, reaction_user
    except asyncio.TimeoutError:
        return None, None
    
class ReactionMenu:
    """A class for handling multi-step reaction-based menus."""

    def __init__(self, ctx: commands.Context, timeout: float = 30.0):
        self.ctx = ctx
        self.bot: Client = ctx.bot
        self.timeout = timeout
        self.message: Optional[discord.Message] = None
        self.target_user: Optional[Union[discord.User, discord.Member]] = ctx.author

    def set_target_user(self, user: Optional[Union[discord.User, discord.Member]]) -> None:
        """Set which user should be allowed to interact with this menu.
        
        Args:
            user: The user who can interact with the menu, or None to allow any user
        """
        self.target_user = user

    async def _update_message(
        self,
        content: str,
        embed: Optional[discord.Embed],
        method: Callable[..., Coroutine[Any, Any, discord.Message]]
    ) -> discord.Message:
        """
        Internal helper to send or edit a message.
        
        Args:
            content: The text content to send
            embed: Optional embed to include
            method: The method to call for sending (ctx.send or ctx.reply)
            
        Returns:
            The sent or edited message
        """
        if self.message is None:
            self.message = await method(content=content, embed=embed)
        else:
            await self.message.edit(content=content, embed=embed)
        return self.message

    async def send(self, content: str, *, embed: Optional[discord.Embed] = None) -> discord.Message:
        """Send or edit the menu message."""
        return await self._update_message(content, embed, self.ctx.send)
    
    async def reply(self, content: str, *, embed: Optional[discord.Embed] = None) -> discord.Message:
        """Reply or edit the menu message."""
        return await self._update_message(content, embed, self.ctx.reply)
    
    async def add_reactions(self, emoji_list: List[str]) -> None:
        """Add a list of reactions to the menu message."""
        if self.message is None:
            raise ValueError("Cannot add reactions before sending a message")
        
        for emoji in emoji_list:
            await self.message.add_reaction(emoji)

    async def wait_for_reaction(self, emoji_list: List[str]) -> Tuple[Optional[str], Optional[Union[discord.User, discord.Member]]]:
        """
        Wait for a reaction from the target user (or any user if target_user is None) and return the selected emoji.
        
        Returns:
            A tuple of (selected_emoji, reacting_user) or (None, None) if timed out
        """
        if self.message is None:
            raise ValueError("Cannot wait for reactions before sending a message")
        
        reaction, user = await wait_for_reaction(
            self.bot, self.message, self.target_user, emoji_list, self.timeout
        )

        if reaction is None:
            return None, None
        
        return str(reaction.emoji), user
    
    async def cleanup(self) -> None:
        """Remove all reactions from the message."""
        if self.message:
            try:
                await self.message.clear_reactions()
            except (discord.errors.Forbidden, discord.errors.HTTPException):
                pass
