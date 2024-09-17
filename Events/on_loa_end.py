import discord
from discord.ext import commands
import os
from Utils.config import config
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["TriMelERM"]
abscenses = db["Abscenses"]


class On_loa_end(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_loa_end(self, objectid: ObjectId):
        result = await abscenses.find_one({"_id": objectid})
        if not result:
            return
        guild = self.client.get_guild(result.get("guild"))
        if not guild:
            return
        channel = guild.get_channel(config.get("loa").get("channel"))
        if not channel:
            return
        if not channel.permissions_for(
            guild.get_member(self.client.user.id)
        ).send_messages:
            return
        msg = await channel.fetch_message(result.get("msg"))
        embed = msg.embeds[0]
        embed.color = discord.Color.orange()
        embed.title = "Leave Ended"
        await msg.reply(embed=embed)
        await abscenses.update_one(
            {"_id": objectid},
            {"$set": {"status": "ended"}},
        )
        user = guild.get_member(result.get("user"))
        if not user:
            return
        await user.send(embed=embed)
        try:
            role = guild.get_role(config.get("loa").get("role"))
            if not role:
                return
            if role in user.roles:
                await user.remove_roles(role)
        except (discord.Forbidden, discord.NotFound):
            return


async def setup(client: commands.Bot) -> None:
    await client.add_cog(On_loa_end(client))
