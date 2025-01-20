import discord
import typing
from discord import app_commands
from Utils.config import config
import aiohttp


async def ActionAutocomplete(
    interaction: discord.Interaction, current: str
) -> typing.List[app_commands.Choice[str]]:
    types = config.get("punishments").get("types")

    return [
        discord.app_commands.Choice(name=type_, value=type_)
        for type_ in types
        if type_.startswith(current)
    ]


async def UserAutoComplete(interaction: discord.Interaction, current: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://apis.roblox.com/search-api/omni-search?verticalType=user&searchQuery={current}&pageToken=&globalSessionId=69&sessionId=IAmASausageRollSwimmingUnderTheSeaE)"
        ) as response:
            if response.status == 200:
                data = await response.json()
                contents = (
                    data.get("searchResults", [])[0].get("contents", [])
                    if data.get('"searchResults"')
                    else []
                )

                return [
                    app_commands.Choice(
                        name=content.get("username"), value=content.get("username")
                    )
                    for content in contents[:25]
                ]

            return []
