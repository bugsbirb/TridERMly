import discord
from discord.ext import commands
import os
from Utils.config import config
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["TriMelERM"]
shifts = db["Shifts"]


class on_shift_break(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_shift_break(self, objectid: ObjectId):
        shift = await shifts.find_one({"_id": objectid})
        if not shift:
            return
        guild = self.client.get_guild(int(shift.get("guild")))
        if not guild:
            return
        channel = guild.get_channel(int(config.get("shifts").get("channel")))
        if not channel:
            return
        author = guild.get_member(shift.get("user"))
        if not author:
            return        
        await channel.send(
            embed=discord.Embed(
                title="Shift Break",
                description = (
                    f"**User:** @{author.name}\n"
                    f"**Started:** <t:{int(shift.get('break'))}>\n"
                    f"**ID:** `{shift.get('_id')}`"
                ),          
                timestamp=discord.utils.utcnow(),
                color=discord.Color.orange(),
            )
            .set_author(name=f"@{author.name}", icon_url=author.display_avatar)
        )        

             


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_shift_break(client))
