import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from datetime import timezone
from roblox import Client
from motor.motor_asyncio import AsyncIOMotorClient
from Utils.config import config
from bson import ObjectId
from Utils.dates import strtotime
from datetime import timedelta, datetime
import pytz

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["TriMelERM"]
abscenses = db["Abscenses"]

Roblox = Client()


class Leaves(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @commands.hybrid_group(name="absence")
    async def absence(self, ctx):
        pass

    @absence.command(description="View all active leaves.")
    async def active(self, ctx: commands.Context):
        loa = config.get("loa")
        permissions = loa.get("manager")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        guild = ctx.guild
        AbcensesResult = await abscenses.find(
            {"guild": guild.id, "status": {"$ne": "ended"}}
        ).to_list(length=None)
        if not AbcensesResult:
            await ctx.send(f"` ❌ ` There are no active leaves.", ephemeral=True)
            return
        description = ""
        embed = discord.Embed(
            title="",
            color=discord.Color.dark_embed(),
            description=description,
        )
        embed.set_thumbnail(url=guild.icon)
        embed.set_author(name=f"{guild.name}", icon_url=guild.icon)
        for abcenses in AbcensesResult:
            embed.add_field(
                name=f"`{abcenses.get('_id')}`",
                value=f"> **User:** <@{abcenses.get('user')}>\n"
                f"> **Reason:** {abcenses.get('reason')}\n"
                f"> **Start:** <t:{int(abcenses.get('start').timestamp())}:R>\n"
                f"> **Ends:** <t:{int(abcenses.get('date').timestamp())}:R>",
                inline=False,
            )
        await ctx.send(embed=embed)

    @absence.command(description="Manage a active leave.")
    @app_commands.describe(member="The member to manage.")
    async def admin(self, ctx: commands.Context, member: discord.Member):
        loa = config.get("loa")
        permissions = loa.get("manager")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        if not member:
            await ctx.send(f"` ❌ ` Please specify a member.", ephemeral=True)
            return
        Result = await abscenses.find_one(
            {
                "user": member.id,
                "status": "accepted",
                "$and": [{"status": {"$ne": "denied"}}, {"status": {"$ne": "ended"}}],
            }
        )
        if not Result:
            await ctx.send(f"` ❌ ` {member.mention} is not on leave.", ephemeral=True)
            return
        await ctx.send(
            embed=discord.Embed(
                description=f"> **Started:** <t:{int(Result.get('start').timestamp())}:R>\n> **Ends:** <t:{int(Result.get('date').timestamp())}:R>\n> **Reason:** {Result.get('reason')}",
                color=discord.Color.dark_embed(),
                timestamp=datetime.now(),
            )
            .set_author(name=f"@{member.name}", icon_url=member.display_avatar)
            .set_footer(text=f"ID: {Result.get('_id')}"),
            view=LoaManage(ctx.author, member, Result.get("_id")),
        )

    @tasks.loop(minutes=10)
    async def CheckAbscenses(self):
        print("[INFO] Checking for abscenses...")
        loa = config.get("loa")
        guilds = self.client.guilds
        for guild in guilds:
            channel = guild.get_channel(loa.get("channel"))
            if not channel:
                continue
            if not channel.permissions_for(
                guild.get_member(self.client.user.id)
            ).send_messages:
                print("[ERROR] I can't send messages in the LOA Channel")
                continue
            AbcensesResult = await abscenses.find({"guild": guild.id}).to_list(
                length=None
            )
            if not AbcensesResult:
                print("[INFO] No abscenses found")
                continue
            for abcenses in AbcensesResult:
                if not abcenses.get("status") == "accepted":
                    continue
                if datetime.now() >= abcenses.get("date"):
                    user = guild.get_member(abcenses.get("user"))
                    if not user:
                        print("[ERROR] Can't find LOA Member")
                        continue
                    if abcenses.get("status", None) == "accepted":
                        if abcenses.get("end", None) == None:
                            await abscenses.update_one(
                                {"_id": abcenses.get("_id")},
                                {"$set": {"end": datetime.now()}},
                            )
                            self.client.dispatch("loa_end", abcenses.get("_id"))
                        else:
                            continue
                    else:
                        continue

    @absence.command(description="Submit a leave request.")
    @app_commands.describe(
        reason="The reason for the leave.",
        duration="The duration of the leave. (e.g. 1d, 2h, 3m)",
    )
    async def request(self, ctx: commands.Context, reason: str, duration: str):
        loa = config.get("loa")
        permissions = loa.get("permissions")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        date = strtotime(duration)
        LOA = await abscenses.find_one({"user": ctx.author.id, "guild": ctx.guild.id})
        if LOA:
            if LOA.get("status") == "pending":
                return await ctx.send(
                    f"` ❌ ` You already have an absence request.", ephemeral=True
                )
            elif LOA.get("status") == "accepted":
                return await ctx.send(
                    f"` ❌ ` You are already on leave.", ephemeral=True
                )
        channel = self.client.get_channel(loa.get("channel"))
        if not channel:
            return await ctx.send(f"` ❌ ` I can't find that channel.", ephemeral=True)
        elif not channel.permissions_for(
            ctx.guild.get_member(self.client.user.id)
        ).send_messages:
            return await ctx.send(
                f"` ❌ ` I don't have permission to send messages in this channel.",
                ephemeral=True,
            )
        logged = await abscenses.insert_one(
            {
                "user": ctx.author.id,
                "guild": ctx.guild.id,
                "date": date,
                "start": datetime.now(),
                "reason": reason,
                "status": "pending",
                "channel": channel.id,
            }
        )
        msg = await channel.send(
            embed=discord.Embed(
                title="Leave Request",
                description=f"> **User:** <@{ctx.author.id}>\n> **Reason:** {reason}\n> **Starts:** <t:{int(datetime.now().timestamp())}:R>\n> **Ends:** <t:{int(date.timestamp())}:R>",
                timestamp=datetime.now(),
                color=discord.Color.dark_embed(),
            )
            .set_author(name=f"{ctx.author.name}", icon_url=ctx.author.display_avatar)
            .set_footer(text=f"ID: {logged.inserted_id}")
            .set_thumbnail(url=ctx.author.display_avatar),
            view=AbcenseApproval(),
        )

        if not logged.inserted_id:
            return await ctx.send(f"` ❌ ` Something went wrong.")
        await abscenses.update_one(
            {"_id": ObjectId(logged.inserted_id)},
            {"$set": {"msg": msg.id}},
        )
        await ctx.send(f"` ✅ ` Your leave request has been sent.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.client.add_view(AbcenseApproval())
        self.CheckAbscenses.start()


class AbcenseApproval(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.green, custom_id="acceptme"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        loa = config.get("loa")
        permissions = loa.get("manager")
        if not any(role.id in permissions for role in interaction.user.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        result = await abscenses.find_one({"msg": interaction.message.id})
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "Leave Accepted"
        embed.set_footer(
            text=f"Accepted By @{interaction.user.name}",
            icon_url=interaction.user.display_avatar,
        )
        await interaction.edit_original_response(embed=embed, view=None)
        await abscenses.update_one(
            {"_id": ObjectId(result.get("_id"))},
            {"$set": {"status": "accepted"}},
        )
        try:
            user = interaction.guild.get_member(result.get("user"))
            if not user:
                return
            role = interaction.guild.get_role(config.get("loa").get("role"))
            if not role:
                return
            if not role in user.roles:
                await user.add_roles(role)
        except (discord.Forbidden, discord.NotFound):
            return
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            return

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="denyme")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        loa = config.get("loa")
        permissions = loa.get("manager")
        if not any(role.id in permissions for role in interaction.user.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        result = await abscenses.find_one({"msg": interaction.message.id})
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "Leave Denied"
        embed.set_footer(
            text=f"Denied By @{interaction.user.name}",
            icon_url=interaction.user.display_avatar,
        )

        await interaction.edit_original_response(embed=embed)
        await abscenses.delete_one(
            {"_id": ObjectId(result.get("_id"))},
        )
        try:
            user = interaction.guild.get_member(result.get("user"))
            if not user:
                return
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                return
        except (discord.Forbidden, discord.NotFound):
            return


class LoaManage(discord.ui.View):
    def __init__(self, author, user, id):
        super().__init__(timeout=None)
        self.author = author
        self.user = user
        self.id = id

    @discord.ui.button(label="End LOA", style=discord.ButtonStyle.red)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author.id != self.author.id:
            await interaction.response.send_message(
                "` ❌ ` This isn't your panel.", ephemeral=True
            )
            return
        loa = config.get("loa")

        permissions = loa.get("manager")
        if not any(role.id in permissions for role in interaction.user.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        result = await abscenses.find_one(
            {"_id": ObjectId(self.id), "status": "accepted"}
        )
        if not result:
            await interaction.response.send_message(
                f"` ❌ ` I couldn't find the specified leave request.", ephemeral=True
            )
            return
        await abscenses.update_one(
            {"_id": ObjectId(result.get("_id"))},
            {"$set": {"end": datetime.now()}},
        )
        await interaction.response.edit_message(
            content=f"` ✅ ` Successfully ended the leave.", view=None, embed=None
        )
        interaction.client.dispatch("loa_end", result.get("_id"))

    @discord.ui.button(label="Extend Time", style=discord.ButtonStyle.green)
    async def extend(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author.id != self.author.id:
            await interaction.response.send_message(
                "` ❌ ` This isn't your panel.", ephemeral=True
            )
            return
        loa = config.get("loa")
        permissions = loa.get("manager")
        if not any(role.id in permissions for role in interaction.user.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        await interaction.response.send_modal(ExtendTime(self.user, self.id))

    @discord.ui.button(label="Extract Time", style=discord.ButtonStyle.red)
    async def extract(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.author.id != self.author.id:
            await interaction.response.send_message(
                "` ❌ ` This isn't your panel.", ephemeral=True
            )
            return
        loa = config.get("loa")
        permissions = loa.get("manager")
        if not any(role.id in permissions for role in interaction.user.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        await interaction.response.send_modal(ExtractTime(self.user, self.id))


class ExtendTime(discord.ui.Modal):
    def __init__(self, user, id):
        super().__init__(title="Extend Time")
        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="e.g. 1d, 2h, 3m",
            style=discord.TextStyle.short,
        )
        self.add_item(self.duration)
        self.user = user
        self.id = id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        loa = config.get("loa")
        DurationValue = self.duration.value.strip()

        if not DurationValue[:-1].isdigit() or DurationValue[-1] not in "dhm":
            await interaction.response.send_message(
                f"` ❌ ` Please enter a valid duration in the format of [number][d/h/m].",
                ephemeral=True,
            )
            return

        try:
            Times = {"d": "days", "h": "hours", "m": "minutes"}
            Unit = Times[DurationValue[-1]]
            ExtendedTime = timedelta(**{Unit: int(DurationValue[:-1])})
        except Exception:
            await interaction.response.send_message(
                f"` ❌ ` An error occurred while processing the time extension.",
                ephemeral=True,
            )
            return

        result = await abscenses.find_one({"_id": ObjectId(self.id)})
        if not result:
            await interaction.response.send_message(
                f"` ❌ ` I couldn't find the specified leave request.", ephemeral=True
            )
            return

        OldDate = result.get("date")
        if OldDate.tzinfo is None:
            OldDate = OldDate.replace(tzinfo=pytz.UTC)

        newdate = OldDate + ExtendedTime
        now = datetime.now(pytz.UTC)

        if newdate < now:
            await interaction.response.send_message(
                f"` ❌ ` The new date cannot be in the past.",
                ephemeral=True,
            )
            return

        await abscenses.update_one(
            {"_id": ObjectId(result.get("_id"))},
            {"$set": {"date": newdate}},
        )
        await interaction.response.edit_message(
            content=f"` ✅ ` Successfully extended the leave.",
            embed=None,
            view=None,
        )


class ExtractTime(discord.ui.Modal):
    def __init__(self, user, id):
        super().__init__(title="Extract Time")
        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="e.g. 1d, 2h, 3m",
            style=discord.TextStyle.short,
        )
        self.add_item(self.duration)
        self.user = user
        self.id = id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        loa = config.get("loa")
        DurationValue = self.duration.value.strip()

        if not DurationValue[:-1].isdigit() or DurationValue[-1] not in "dhm":
            await interaction.response.send_message(
                f"` ❌ ` Please enter a valid duration in the format of [number][d/h/m].",
                ephemeral=True,
            )
            return

        try:
            Times = {"d": "days", "h": "hours", "m": "minutes"}
            Unit = Times[DurationValue[-1]]
            ExtractedTime = timedelta(**{Unit: int(DurationValue[:-1])})
        except Exception:
            await interaction.response.send_message(
                f"` ❌ ` An error occurred while processing the time extraction.",
                ephemeral=True,
            )
            return

        result = await abscenses.find_one({"_id": ObjectId(self.id)})
        if not result:
            await interaction.response.send_message(
                f"` ❌ ` I couldn't find the specified leave request.", ephemeral=True
            )
            return

        OldDate = result.get("date")
        if OldDate.tzinfo is None:
            OldDate = OldDate.replace(tzinfo=pytz.UTC)

        newdate = OldDate - ExtractedTime
        now = datetime.now(pytz.UTC)

        if newdate < now:
            await interaction.response.send_message(
                f"` ❌ ` The new date cannot be in the past.",
                ephemeral=True,
            )
            return

        await abscenses.update_one(
            {"_id": ObjectId(result.get("_id"))},
            {"$set": {"date": newdate}},
        )
        await interaction.response.edit_message(
            content=f"` ✅ ` Successfully extracted time from the leave.",
            embed=None,
            view=None,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Leaves(client))
