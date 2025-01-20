import discord
from discord.ext import commands
from roblox import UserNotFound, Client
from Utils.config import config
from bson import ObjectId
from Utils.Roblox import RobloxThumbnail


roblox = Client()
class on_moderate(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @commands.Cog.listener()
    async def on_moderation(self, objectid: ObjectId):

        moderation = await self.client.moderations.find_one({"_id": objectid})
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
            user = await roblox.get_user_by_username(moderation.get("username"))
        except UserNotFound:
            return
        if not user:
            return

        proof = moderation.get("proof")
        msg = await channel.send(
            embed=discord.Embed(
                title="Moderation Issued",
                description = (
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
        print(proof)
        await self.client.moderations.update_one(
            {"_id": objectid}, {"$set": {"message": msg.id, "jump": msg.jump_url}}
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(on_moderate(client))
