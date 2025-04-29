import os
from typing import List
import discord
from discord.ext import commands
from discord import app_commands


def find_similar_commands(input_cmd: str, commands_list: List[commands.Command], score_limit: int = 2) -> List[commands.Command]:
    """Find similar commands using Levenshtein distance"""
    def levenshtein_distance(a: str, b: str) -> int:
        if len(a) < len(b):
            return levenshtein_distance(b, a)
        if not b:
            return len(a)
        
        previous_row = range(len(b) + 1)
        for i, c1 in enumerate(a):
            current_row = [i + 1]
            for j, c2 in enumerate(b):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
    
    similarities = [(cmd, levenshtein_distance(input_cmd, cmd.name)) for cmd in commands_list]
    similarities.sort(key=lambda x: x[1])
    return [cmd for cmd, score in similarities if score <= score_limit]

def app_command_main_guild():
    """Decorator for restricting app commands to the main guild"""
    return app_commands.guilds(discord.Object(id=int(os.getenv('GUILD_ID'))))