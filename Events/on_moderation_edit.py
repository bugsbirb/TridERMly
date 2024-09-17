import discord
from discord.ext import commands
from roblox import Client, UserNotFound
import os
from Utils.config import config
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from Utils.Roblox import RobloxThumbnail


MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["TriMelERM"]
moderations = db["Moderations"]
Roblox = Client()


class on_moderate_edit(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_moderation_edit(self, objectid: ObjectId, voided=False):
        moderation = await moderations.find_one({"_id": objectid})
        if not moderation:
            return
        guild = self.client.get_guild(int(moderation.get("guild")))
        if not guild:
            return
        channel = guild.get_channel(int(config.get("punishments").get("channel")))
        if not channel:
            return
        author = guild.get_member(moderation.get("author"))
        if not author:
            return
        try:
            user = await Roblox.get_user_by_username(moderation.get("username"))
        except UserNotFound:
            return
        if not user:
            return
        message = moderation.get("message")
        proof = moderation.get("proof")
        if not message:
            return
        vmsg = ""
        msg = await channel.fetch_message(message)
        if voided is True:
            vmsg = " (Voided)"
        await msg.edit(
            embed=discord.Embed(
                title=f"Moderation Issued{vmsg}",
                description=(
                    f"**User:** @{moderation.get('username')} (`{moderation.get('UserID')}`)\n"
                    f"**Punishment:** {moderation.get('action')}\n"
                    f"**Reason:** {moderation.get('reason')}\n"
                    f"**ID** `{moderation.get('_id')}`"
                    f"\n{'🖼️ **Proof Below**' if proof else ''}"
                ),
                timestamp=discord.utils.utcnow(),
                color=discord.Color.green(),
            )
            .set_author(name=f"@{user.name}", icon_url=await RobloxThumbnail(user.id))
            .set_footer(
                text=f"Moderated By @{author.name}",
                icon_url=author.display_avatar,
            )
            .set_image(url=proof if proof else None)
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_moderate_edit(client))
