import asyncio
from typing import Callable, List, Mapping, Optional, Union
import discord
from discord.ext import commands

_PageType = Union[str, discord.Embed]
_PageList = List[_PageType]
_ControlCallable = Callable[[commands.Context, _PageList, discord.Message, int, float], int]

DEFAULT_CONTROLS: Mapping[str, _ControlCallable] = {
    "⬅️": lambda ctx, pages, message, page, timeout: (page - 1) if page > 0 else len(pages) - 1,
    "❌": lambda ctx, pages, message, page, timeout: -1,
    "➡️": lambda ctx, pages, message, page, timeout: (page + 1) if page < len(pages) - 1 else 0,
}

async def menu(
    ctx: commands.Context,
    pages: _PageList,
    controls: Optional[Mapping[str, _ControlCallable]] = None,
    message: Optional[discord.Message] = None,
    page: int = 0,
    timeout: float = 30.0,
    *,
    user: Optional[discord.User] = None,
) -> Optional[discord.Message]:
    """
    Creates a reaction-based menu for navigating pages.
    
    Parameters:
    -----------
    ctx: commands.Context
        The context of the command.
    pages: List[str] or List[discord.Embed]
        The pages to display in the menu.
    controls: Optional[Mapping[str, _ControlCallable]]
        Custom control emojis and their functions.
    message: Optional[discord.Message]
        An existing message to edit. If None, a new message will be sent.
    page: int
        The starting page number (0-based index).
    timeout: float
        How long to wait for a reaction (in seconds).
    user: Optional[discord.User]
        The user who can interact with the menu. If None, only the command invoker can interact.
    """

    if not pages:
        raise ValueError("Cannot create a menu with no pages.")
    
    if not message:
        if isinstance(pages[page], discord.Embed):
            message = await ctx.send(embed=pages[page])
        else:
            message = await ctx.send(pages[page])

    active_controls = controls if controls is not None else DEFAULT_CONTROLS

    try:
        for emoji in active_controls.keys():
            await message.add_reaction(emoji)
    except discord.errors.Forbidden:
        return message
    
    def react_check(reaction: discord.Reaction, user_check: discord.User) -> bool:
        """Check if reaction is valid"""
        return (
            reaction.message.id == message.id
            and str(reaction.emoji in active_controls)
            and (user_check == ctx.author if user is None else user_check == user)
        )
    
    current_page = page
    bot: commands.Bot = ctx.bot

    while True:
        try:
            reaction: discord.Reaction
            user_reacted: discord.User
            reaction, user_reacted = await bot.wait_for(
                'reaction_add',
                check=react_check,
                timeout=timeout
            )
        except asyncio.TimeoutError:
            try:
                await message.reactions.clear()
            except (discord.errors.Forbidden, discord.errors.NotFound):
                pass
            break

        try:
            await message.remove_reaction(reaction, user_reacted)
        except (discord.errors.Forbidden, discord.errors.NotFound):
            pass

        control_func = active_controls[str(reaction.emoji)]
        new_page = control_func(ctx, pages, message, current_page, timeout)

        if new_page == -1:
            try:
                await message.clear_reactions()
            except (discord.errors.Forbidden, discord.errors.NotFound):
                pass
            break

        if 0 <= new_page < len(pages):
            current_page = new_page
            try:
                if isinstance(pages[current_page], discord.Embed):
                    await message.edit(embed=pages[current_page], content=None)
                else:
                    await message.edit(content=pages[current_page], embed=None)
            except (discord.errors.Forbidden, discord.errors.NotFound):
                break

    return message