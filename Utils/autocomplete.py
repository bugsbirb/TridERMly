import discord
import typing
from discord import app_commands
from Utils.config import config


async def ActionAutocomplete(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    types = config.get("punishments").get("types")

    return [
        discord.app_commands.Choice(name=type_, value=type_)
        for type_ in types
        if type_.startswith(current)
    ]
