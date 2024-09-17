import discord
from discord.ext import commands
from discord import app_commands
import os
import time

from Utils.autocomplete import ActionAutocomplete
from roblox import Client
from motor.motor_asyncio import AsyncIOMotorClient
from Utils.Roblox import RobloxThumbnail
from Utils.config import config
from bson import ObjectId
import Utils.paginations as Paginator

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["TriMelERM"]
moderations = db["Moderations"]

Roblox = Client()


class Moderations(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_group(name="punishment")
    async def punishment(self, ctx):
        pass

    @punishment.command(description="Moderate a roblox user")
    @app_commands.autocomplete(action=ActionAutocomplete)
    @app_commands.describe(
        username="The Roblox username of the user to moderate",
        action="The action to take against the user",
        reason="The reason for moderating the user",
        proof="Optional proof of the offense",
    )
    async def issue(
        self,
        ctx: commands.Context,
        username: str,
        action: str,
        reason: str,
        proof: discord.Attachment = None,
    ):
        punishment = config.get("punishments")
        permissions = punishment.get("permissions")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        channel = ctx.guild.get_channel(int(punishment.get("channel")))

        if not channel:
            await ctx.send(f"` ❌ ` The channel could not be found.")
            return
        client = ctx.guild.get_member(self.client.user.id)
        if channel.permissions_for(client).send_messages is False:
            return await ctx.send(
                content=f"` ❌ `  oi I can't send messages in the infraction channel!!",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        user = await Roblox.get_user_by_username(username)
        if not user:
            await ctx.send(f"` ❌ ` @**{username}** could not be found.")
            return
        moderation = await moderations.insert_one(
            {
                "username": username,
                "action": action,
                "reason": reason,
                "UserID": user.id,
                "author": ctx.author.id,
                "time": time.time(),
                "guild": ctx.guild.id,
            }
        )
        if not moderation.inserted_id:
            await ctx.send(f"` ❌ ` Something went wrong.")
            return
        self.client.dispatch("moderation", moderation.inserted_id)
        await ctx.send(
            embed=discord.Embed(
                title="Successfully Moderated",
                description=(
                    f"**User:** @{username} (`{user.id}`)\n"
                    f"**Punishment:** {action}\n"
                    f"**Reason:** {reason}\n"
                    f"**ID** `{moderation.inserted_id}`"
                    f"\n{'🖼️ **Proof Below**' if proof else ''}"
                ),
                timestamp=discord.utils.utcnow(),
                color=discord.Color.green(),
            )
            .set_author(name=f"@{username}", icon_url=await RobloxThumbnail(user.id))
            .set_footer(
                text=f"Moderated By @{ctx.author.name}",
                icon_url=ctx.author.display_avatar,
            )
            .set_image(url=proof.url if proof else None)
        )

    @punishment.command(description="Manage a existing moderation.")
    async def manage(self, ctx: commands.Context, id: str):
        punishment = config.get("punishments")
        permissions = punishment.get("permissions")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        moderation = await moderations.find_one({"_id": ObjectId(id)})
        if not moderation:
            await ctx.send(f"` ❌ ` I couldn't find the specified punishment id.")
            return
        proof = moderation.get("proof")
        embed = (
            discord.Embed(
                title="Moderation",
                description=f"**User:** @{moderation.get('username')} (`{moderation.get('UserID')}`)\n**Punishment:** {moderation.get('action')}\n**Reason:** {moderation.get('reason')}\n**ID** `{moderation.get('_id')}`\n{'🖼️ **Proof Below**' if proof else ''}",
                timestamp=discord.utils.utcnow(),
                color=discord.Color.dark_embed(),
            )
            .set_author(
                name=f"@{moderation['username']}",
                icon_url=await RobloxThumbnail(moderation.get("UserID")),
            )
            .set_footer(
                text=f"Moderated By @{ctx.guild.get_member(moderation.get('author')).name}",
                icon_url=ctx.guild.get_member(moderation.get("author")).display_avatar,
            )
            .set_image(url=proof if proof else None)
        )
        await ctx.send(
            embed=embed, view=PunishmentManage(moderation.get("_id"), ctx.author)
        )

    @punishment.command(description="View a user's punishments")
    async def view(self, ctx: commands.Context, username: str):
        punishment = config.get("punishments")
        permissions = punishment.get("permissions")

        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return

        user = await Roblox.get_user_by_username(username)
        if not user:
            await ctx.send(f"` ❌ ` @**{username}** could not be found.")
            return

        moderation = await moderations.find({"UserID": user.id}).to_list(length=750)
        if not moderation:
            await ctx.send(f"` ❌ ` @**{username}** has no punishments.")
            return

        embed = discord.Embed(
            title=f"Punishments for @{username}",
            color=discord.Color.dark_embed(),
        )
        embeds = []
        items = 0
        embed = discord.Embed()
        for i, mod in enumerate(moderation):
            embed.description = (
                (embed.description or "")
                + f"`{i + 1}` **Action:** {mod.get('action')}\n"
                f"> **Reason:** {mod.get('reason')}\n"
                f"> **Issuer:** <@{mod.get('author')}>\n"
                f"> **ID** `{mod.get('_id')}`\n"
                f"> **Time:** <t:{int(mod.get('time'))}:R>\n"
                f"> **Proof:** {mod.get('proof') if mod.get('proof') else 'None'}\n"
            )
            items += 1
            if items % 10 == 0:
                embed.set_author(name="Punishments", icon_url=ctx.guild.icon)
                embed.set_thumbnail(url=ctx.guild.icon)
                embed.color = discord.Color.dark_embed()
                embeds.append(embed)
                embed = discord.Embed()
                items = 0

        if items > 0:
            embeds.append(embed)

        if len(embeds) == 0:
            await ctx.send("No punishments found.", ephemeral=True)
            return
        PreviousButton = discord.ui.Button(label="<")
        NextButton = discord.ui.Button(label=">")
        FirstEmbedButton = discord.ui.Button(label="<<")
        LastEmbedButton = discord.ui.Button(label=">>")

        if len(embeds) <= 1:
            PreviousButton.disabled = True
            NextButton.disabled = True
            FirstEmbedButton.disabled = True
            LastEmbedButton.disabled = True
        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstEmbedButton,
            LastEmbedButton=LastEmbedButton,
            InitialPage=0,
            timeout=1080,
        )
        await paginator.start(ctx, pages=embeds)

    @punishment.command(description="View all punishments")
    async def all(self, ctx: commands.Context):
        punishment = config.get("punishments")
        permissions = punishment.get("permissions")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        moderation = await moderations.find({"guild": ctx.guild.id}).to_list(length=750)
        if not moderation:
            await ctx.send(f"` ❌ ` No punishments have been issued.")
            return
        embed = discord.Embed(
            title=f"",
            color=discord.Color.dark_embed(),
        )
        embeds = []
        items = 0
        embed = discord.Embed()
        embed.set_author(name="Punishments", icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.color = discord.Color.dark_embed()
        for i, mod in enumerate(moderation):
            embed.description = (
                (embed.description or "")
                + f"`{i + 1}` **User:** @{mod.get('username')} (`{mod.get('UserID')}`)\n"
                f"> **Action:** {mod.get('action')}\n"
                f"> **Reason:** {mod.get('reason')}\n"
                f"> **Issuer:** <@{mod.get('author')}>\n"
                f"> **Time:** <t:{int(mod.get('time'))}:R>\n"
                f"> **ID** `{mod.get('_id')}`\n"
                f"> **Proof:** {mod.get('proof') if mod.get('proof') else 'None'}\n"
            )
            items += 1
            if items % 10 == 0:
                embed.set_author(name="Punishments", icon_url=ctx.guild.icon.url)
                embed.set_thumbnail(url=ctx.guild.icon)
                embed.color = discord.Color.dark_embed()
                embeds.append(embed)
                embed = discord.Embed()
                items = 0

        if items > 0:
            embeds.append(embed)

        if len(embeds) == 0:
            await ctx.send("No punishments found.", ephemeral=True)
            return

        PreviousButton = discord.ui.Button(label="<")
        NextButton = discord.ui.Button(label=">")
        FirstEmbedButton = discord.ui.Button(label="<<")
        LastEmbedButton = discord.ui.Button(label=">>")

        if len(embeds) <= 1:
            PreviousButton.disabled = True
            NextButton.disabled = True
            FirstEmbedButton.disabled = True
            LastEmbedButton.disabled = True
        paginator = Paginator.Simple(
            PreviousButton=PreviousButton,
            NextButton=NextButton,
            FirstEmbedButton=FirstEmbedButton,
            LastEmbedButton=LastEmbedButton,
            InitialPage=0,
            timeout=1080,
        )
        await paginator.start(ctx, pages=embeds)


class PunishmentManage(discord.ui.View):
    def __init__(self, id, author):
        super().__init__()
        self.id = id
        self.author = author

    @discord.ui.button(label="Void", style=discord.ButtonStyle.danger)
    async def void(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author.id != interaction.user.id:
            await interaction.response.send_message(
                "` ❌ ` This isn't your panel.", ephemeral=True
            )
            return
        moderation = await moderations.find_one({"_id": ObjectId(self.id)})
        if not moderation:
            await interaction.response.send_message(
                "` ❌ ` I couldn't find the specified punishment id.", ephemeral=True
            )
            return
        await interaction.response.edit_message(
            "` ✅ ` Successfully voided the punishment.", embed=None, view=None
        )
        interaction.client.dispatch("moderation_edit", self.id, voided=True)
        await moderations.delete_one({"_id": self.id})

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.blurple)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author.id != interaction.user.id:
            await interaction.response.send_message(
                "` ❌ ` This isn't your panel.", ephemeral=True
            )
            return
        await interaction.response.send_modal(EditModal(self.id))


class EditModal(discord.ui.Modal, title="Edit Punishment"):
    def __init__(self, id):
        super().__init__()
        self.action = discord.ui.TextInput(
            label="Action", style=discord.TextStyle.short
        )
        self.reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.long)
        self.proof = discord.ui.TextInput(
            label="Proof", placeholder="(Image URL)", style=discord.TextStyle.long
        )
        self.id = id
        self.add_item(self.action)
        self.add_item(self.reason)
        self.add_item(self.proof)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        moderation = await moderations.find_one({"_id": ObjectId(self.id)})
        if not moderation:
            await interaction.response.send_message(
                "` ❌ ` I* couldn't find the specified punishment id.", ephemeral=True
            )
            return
        await moderations.update_one(
            {"_id": self.id},
            {
                "$set": {
                    "action": self.action.value,
                    "reason": self.reason.value,
                    "proof": self.proof.value,
                }
            },
        )
        await interaction.response.edit_message(
            content="` ✅ ` Successfully edited the punishment.", embed=None, view=None
        )
        interaction.client.dispatch("moderation_edit", self.id, voided=False)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Moderations(client))
