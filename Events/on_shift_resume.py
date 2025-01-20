import discord
from discord.ext import commands
from Utils.config import config
from bson import ObjectId


class On_shift_resume(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_shift_resume(self, objectid: ObjectId):
        shift = await self.client.shifts.find_one({"_id": objectid})
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
                title="Shift Resumed",
                description = (
                    f"**User:** @{author.name}\n"
                    f"**Started:** <t:{int(shift.get('start'))}:R>\n"
                    f"**ID:** `{shift.get('_id')}`"
                ),          
                timestamp=discord.utils.utcnow(),
                color=discord.Color.green(),
            )
            .set_author(name=f"@{author.name}", icon_url=author.display_avatar)
        )        
        

             


async def setup(client: commands.Bot) -> None:
    await client.add_cog(On_shift_resume(client))
