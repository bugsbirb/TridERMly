import discord
from discord.ext import commands
import os
import time
from datetime import timedelta
from roblox import Client
from motor.motor_asyncio import AsyncIOMotorClient
from Utils.config import config
from bson import ObjectId
from Utils.paginations import ActivePagination, LeaderboardPagination

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["TriMelERM"]
shifts = db["Shifts"]

Roblox = Client()


class Shifts(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_group(name="shift")
    async def shift(self, ctx: commands.Context):
        pass
    
    @shift.command(name="clear", description="Clear all shifts")
    async def clear(self, ctx: commands.Context):
        shift = config.get("shifts")
        permissions = shift.get("manager")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return

        await shifts.delete_many({'guild': ctx.guild.id})
        await ctx.send(f"` ✅ ` All shifts have been cleared.", ephemeral=True)


    @shift.command(name="manage", description="Manage your shift")
    async def manage(self, ctx: commands.Context):
        shift = config.get("shifts")
        permissions = shift.get("permissions")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return

        embed = discord.Embed(color=discord.Color.dark_embed())
        view = ShiftManage(ctx.author)

        embed.set_author(
            name=f"@{ctx.author.name}", icon_url=ctx.author.display_avatar.url
        )
        AllShifts = await shifts.find({"user": ctx.author.id, 'guild': ctx.guild.id}).to_list(length=100)
        if AllShifts:
            ShiftResult = await shifts.find_one(
                {"user": ctx.author.id, "status": {"$ne": "inactive"}}
            )
            if not ShiftResult:
                AllShiftTime = sum(
                    (timedelta(seconds=shift.get("duration")) for shift in AllShifts),
                    timedelta(0),
                )
                total_hours, remainder = divmod(AllShiftTime.total_seconds(), 3600)
                total_minutes, total_seconds = divmod(remainder, 60)

                Time = (
                    f"{int(total_hours)}h " * (total_hours > 0)
                    + f"{int(total_minutes)}m " * (total_minutes > 0)
                    + f"{int(total_seconds)}s"
                ).strip()

                TotalShifts = await shifts.count_documents({"user": ctx.author.id, 'guild': ctx.guild.id})

                embed.add_field(
                    name="Information",
                    value=f"> **Shifts:** {TotalShifts}\n> **Total Time:** {Time}",
                )

            if ShiftResult:
                if ShiftResult.get("status") == "Active":
                    embed.title = "Active Shift"
                    embed.color = discord.Color.green()
                elif ShiftResult.get("status") == "Break":
                    embed.title = "On Break"
                    embed.color = discord.Color.orange()
                embed.add_field(
                    name="Current Shift",
                    value=f"> **Status:** {ShiftResult.get('status')}\n> **Started:** <t:{int(ShiftResult.get('start'))}:R>",
                    inline=False,
                )
                if ShiftResult.get("status") == "Break":
                    view.Break.disabled = False
                    view.start.disabled = True
                    view.end.disabled = True
                elif ShiftResult.get("status") == "Active":
                    view.Break.disabled = False
                    view.end.disabled = False
                    view.start.disabled = True
        else:
            embed.add_field(
                name="Information",
                value=f"> **Shifts:** 0\n> **Total Time:** None",
                inline=False,
            )
            view.start.disabled = False
            view.Break.disabled = True
            view.end.disabled = True
        view.remove_item(view.addtime)
        view.remove_item(view.removetime)
        view.remove_item(view.voidshift)

        await ctx.send(embed=embed, view=view)

    @shift.command(name="admin", description="Manage all shifts")
    async def admin(self, ctx: commands.Context, staff: discord.Member):
        shift = config.get("shifts")
        permissions = shift.get("manager")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        if not staff:
            await ctx.send(
                f"` ❌ ` Please specify a staff member to manage.", ephemeral=True
            )
            return
        embed = discord.Embed(color=discord.Color.dark_embed())
        view = ShiftManage(staff)

        embed.set_author(name=f"@{staff.name}", icon_url=staff.display_avatar.url)
        AllShifts = await shifts.find({"user": staff.id, 'guild': ctx.guild.id}).to_list(length=100)
        if AllShifts:
            ShiftResult = await shifts.find_one(
                {"user": staff.id, "status": {"$ne": "inactive"}}
            )
            if not ShiftResult:
                AllShiftTime = sum(
                    (timedelta(seconds=shift.get("duration")) for shift in AllShifts),
                    timedelta(0),
                )
                total_hours, remainder = divmod(AllShiftTime.total_seconds(), 3600)
                total_minutes, total_seconds = divmod(remainder, 60)

                Time = (
                    f"{int(total_hours)}h " * (total_hours > 0)
                    + f"{int(total_minutes)}m " * (total_minutes > 0)
                    + f"{int(total_seconds)}s"
                ).strip()

                TotalShifts = await shifts.count_documents({"user": staff.id, 'guild': ctx.guild.id})

                embed.add_field(
                    name="Information",
                    value=f"> **Shifts:** {TotalShifts}\n> **Total Time:** {Time}",
                )

            if ShiftResult:
                if ShiftResult.get("status") == "Active":
                    embed.title = "Active Shift"
                    embed.color = discord.Color.green()
                elif ShiftResult.get("status") == "Break":
                    embed.title = "On Break"
                    embed.color = discord.Color.orange()
                embed.add_field(
                    name="Current Shift",
                    value=f"> **Status:** {ShiftResult.get('status')}\n> **Started:** <t:{int(ShiftResult.get('start'))}:R>",
                    inline=False,
                )
                if ShiftResult.get("status") == "Break":
                    view.Break.disabled = False
                    view.start.disabled = True
                    view.end.disabled = True
                elif ShiftResult.get("status") == "Active":
                    view.Break.disabled = False
                    view.end.disabled = False
                    view.start.disabled = True
        else:
            embed.add_field(
                name="Information",
                value=f"> **Shifts:** 0\n> **Total Time:** None",
                inline=False,
            )
            view.start.disabled = False
            view.Break.disabled = True
            view.end.disabled = True

        await ctx.send(embed=embed, view=view)

    @shift.command(name="active")
    async def active(self, ctx: commands.Context):
        shift = config.get("shifts")
        permissions = shift.get("permissions")
        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return

        StaffMembers = [
            member
            for role_id in permissions
            for member in ctx.guild.get_role(role_id).members
        ]
        ActiveShifts = await shifts.find({"status": "Active", 'guild': ctx.guild.id}).to_list(length=100)
        ActiveStaff = [
            member
            for shift in ActiveShifts
            for member in StaffMembers
            if member.id == shift.get("user")
        ]

        if ActiveStaff:
            ActiveStaffD = {
                member.id: await shifts.find_one(
                    {"user": member.id, "status": "Active", 'guild': ctx.guild.id}
                )
                for member in ActiveStaff
            }

            description = ""
            for MemberID in list(ActiveStaffD.keys())[:30]:
                ShiftResult = ActiveStaffD[MemberID]
                description += f"> **{ctx.guild.get_member(MemberID).mention}** • <t:{int(ShiftResult.get('start'))}:R>\n"

            embed = discord.Embed(
                title="Active Shifts",
                color=discord.Color.dark_embed(),
                description=description,
            )
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            embed.set_thumbnail(url=ctx.guild.icon)
            view = ActivePagination(ctx.author, ActiveStaffD)
            if (len(ActiveStaff) - 30) > 0:
                view.next.disabled = False
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(f"` ❌ ` There are no active shifts.", ephemeral=True)

    @shift.command(name="leaderboard", description="View the leaderboard")
    async def leaderboard(self, ctx: commands.Context):
        shift = config.get("shifts")
        permissions = shift.get("permissions")

        if not any(role.id in permissions for role in ctx.author.roles):
            await ctx.send(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return

        StaffMembers = [
            member
            for role_id in permissions
            for member in ctx.guild.get_role(role_id).members
        ]

        AllShifts = await shifts.find({"guild": ctx.guild.id}).to_list(length=750)
        if not AllShifts:
            await ctx.send(f"` ❌ ` There are no shifts to display.", ephemeral=True)
            return

        ShiftDurations = {}
        for shift in AllShifts:
            UserId = shift.get("user")
            duration = shift.get("duration", 0)
            ShiftDurations[UserId] = ShiftDurations.get(UserId, 0) + duration

        LambaStaff = sorted(
            StaffMembers,
            key=lambda member: ShiftDurations.get(member.id, 0),
            reverse=True,
        )

        description = ""
        for i, member in enumerate(LambaStaff[:10]):
            duration = ShiftDurations.get(member.id, 0)
            total_hours, remainder = divmod(duration, 3600)
            total_minutes, total_seconds = divmod(remainder, 60)

            Time = (
                f"{int(total_hours)}h " * (total_hours > 0)
                + f"{int(total_minutes)}m " * (total_minutes > 0)
                + f"{int(total_seconds)}s"
            ).strip()

            description += f"**{i + 1}.** {member.mention} • {Time}\n"

        embed = discord.Embed(
            title="Shift Leaderboard",
            color=discord.Color.dark_embed(),
            description=description,
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)

        embed.set_thumbnail(url=ctx.guild.icon)

        view = LeaderboardPagination(ctx.author, ShiftDurations, LambaStaff, 10)
        if (len(LambaStaff) - 10) > 0:
            view.next.disabled = False
        await ctx.send(embed=embed, view=view)


class ShiftManage(discord.ui.View):
    def __init__(self, author: discord.Member, manager: bool = False):
        super().__init__()
        self.author = author
        self.manager = manager

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author
        if not self.manager:
            if self.author.id != self.author.id:
                await interaction.response.send_message(
                    "` ❌ ` This isn't your panel.", ephemeral=True
                )
                return
        ShiftResult = await shifts.find_one(
            {"user": author.id, "status": {"$ne": "inactive", "guild": interaction.guild.id}}
        )
        if ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` You already have an active shift.", ephemeral=True
            )
            return
        shift = await shifts.insert_one(
            {
                "user": self.author.id,
                "start": time.time(),
                "duration": 0,
                "status": "Active",
                "guild": interaction.guild.id,
            }
        )
        embed = discord.Embed(title="Shift Started", color=discord.Color.green())
        embed.set_author(
            name=f"@{author.name}",
            icon_url=author.display_avatar.url,
        )
        embed.add_field(
            name="Current Shift",
            value=f"> **Status:** Active\n> **Started:** <t:{int(time.time())}>",
        )
        self.Break.disabled = False
        self.end.disabled = False
        self.start.disabled = True
        Online = interaction.guild.get_role(config.get("shifts").get("online"))
        try:
            if Online:
                if not Online in author.roles:
                    await author.add_roles(Online)
        except discord.Forbidden:
            pass
        await interaction.response.edit_message(embed=embed, view=self)

        interaction.client.dispatch("shift_start", shift.inserted_id)

    @discord.ui.button(label="Break", style=discord.ButtonStyle.blurple)
    async def Break(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = self.author
        if not self.manager:
            if self.author.id != self.author.id:
                await interaction.response.send_message(
                    "` ❌ ` This isn't your panel.", ephemeral=True
                )
                return

        ShiftResult = await shifts.find_one(
            {"user": author.id, "status": {"$ne": "inactive", "guild": interaction.guild.id}}
        )

        if not ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` You don't have an active shift.", ephemeral=True
            )
            return

        CurrentTime = time.time()

        if ShiftResult.get("status") == "Break":
            BreakDuration = CurrentTime - ShiftResult.get("break")
            UpdatedTime = ShiftResult.get("start") + BreakDuration
            await shifts.update_one(
                {"_id": ShiftResult.get("_id")},
                {
                    "$set": {"status": "Active", "start": UpdatedTime},
                    "$unset": {"break": ""},
                },
            )
            embed = discord.Embed(title="Shift Resumed", color=discord.Color.green())
            embed.set_author(
                name=f"@{self.author.name}",
                icon_url=self.author.display_avatar.url,
            )
            embed.add_field(
                name="Current Shift",
                value=f"> **Status:** Active\n> **Started:** <t:{int(UpdatedTime)}>",
            )
            self.Break.label = "Break"
            self.Break.style = discord.ButtonStyle.blurple
            interaction.client.dispatch("shift_resume", ShiftResult.get("_id"))

        else:
            Break = interaction.guild.get_role(config.get("shifts").get("break"))
            Online = interaction.guild.get_role(config.get("shifts").get("online"))
            try:
                if Break and Online:
                    await self.author.add_roles(Break)
                    await self.author.remove_roles(Online)
            except discord.Forbidden:
                pass
            WorkedTime = CurrentTime - ShiftResult.get("start")
            TotalDuration = ShiftResult.get("duration", 0) + WorkedTime
            await shifts.update_one(
                {"_id": ShiftResult.get("_id")},
                {
                    "$set": {
                        "status": "Break",
                        "break": CurrentTime,
                        "duration": TotalDuration,
                    }
                },
            )
            embed = discord.Embed(title="On Break", color=discord.Color.orange())
            embed.set_author(
                name=f"@{self.author.name}",
                icon_url=self.author.display_avatar.url,
            )
            embed.add_field(
                name="Current Shift",
                value=f"> **Status:** Break\n> **Started:** <t:{int(ShiftResult.get('start'))}:R>",
            )
            self.Break.label = "End Break"
            self.Break.style = discord.ButtonStyle.green

            interaction.client.dispatch("shift_break", ShiftResult.get("_id"))

        self.end.disabled = False
        self.start.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="End", style=discord.ButtonStyle.red)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.manager:
            if self.author.id != self.author.id:
                await interaction.response.send_message(
                    "` ❌ ` This isn't your panel.", ephemeral=True
                )
                return

        ShiftResult = await shifts.find_one(
            {"user": self.author.id, "status": {"$ne": "inactive"}, 'guild': interaction.guild.id}
        )
        if not ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` You don't have an active shift.", ephemeral=True
            )
            return

        CurrentTime = time.time()

        if ShiftResult.get("status") == "Break":
            TotalDuration = ShiftResult.get("duration", 0)
        else:
            WorkedTime = CurrentTime - ShiftResult.get("start")
            TotalDuration = ShiftResult.get("duration", 0) + WorkedTime

        await shifts.update_one(
            {"_id": ShiftResult.get("_id")},
            {
                "$set": {
                    "status": "inactive",
                    "duration": TotalDuration,
                }
            },
        )

        embed = discord.Embed(title="Shift Ended", color=discord.Color.red())
        embed.set_author(
            name=f"@{self.author.name}",
            icon_url=self.author.display_avatar.url,
        )
        embed.add_field(
            name="Current Shift",
            value=f"> **Status:** Inactive\n> **Started:** <t:{int(ShiftResult.get('start'))}:R>\n> **Ended:** <t:{int(CurrentTime)}:R>",
        )

        self.Break.disabled = True
        self.end.disabled = True
        self.start.disabled = False
        Online = interaction.guild.get_role(config.get("shifts").get("online"))
        Break = interaction.guild.get_role(config.get("shifts").get("break"))
        try:
            if Online and Break:
                if Online in self.author.roles:
                    await self.author.remove_roles(Online)
                if Break in self.author.roles:
                    await self.author.remove_roles(Break)
        except discord.Forbidden:
            pass
        await interaction.response.edit_message(embed=embed, view=self)
        interaction.client.dispatch("shift_end", ShiftResult.get("_id"))

    @discord.ui.button(label="Add Time", style=discord.ButtonStyle.green, row=2)
    async def addtime(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not self.manager:
            if self.author.id != self.author.id:
                await interaction.response.send_message(
                    "` ❌ ` This isn't your panel.", ephemeral=True
                )
                return

        ShiftResult = await shifts.find_one(
            {"user": self.author.id, "status": {"$ne": "inactive", 'guild': interaction.guild.id}}
        )
        if not ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` You don't have an active shift.", ephemeral=True
            )
            return
        await interaction.response.send_modal(
            AddTime(self.author, ShiftResult.get("_id"))
        )

    @discord.ui.button(label="Remove Time", style=discord.ButtonStyle.danger, row=2)
    async def removetime(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not self.manager:
            if self.author.id != self.author.id:
                await interaction.response.send_message(
                    "` ❌ ` This isn't your panel.", ephemeral=True
                )
                return
        ShiftResult = await shifts.find_one(
            {"user": self.author.id, "status": {"$ne": "inactive", 'guild': interaction.guild.id}}
        )
        if not ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` You don't have an active shift.", ephemeral=True
            )
            return
        await interaction.response.send_modal(
            RemoveTime(self.author, ShiftResult.get("_id"))
        )

    @discord.ui.button(label="Void Shift", style=discord.ButtonStyle.danger, row=2)
    async def voidshift(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not self.manager:
            if self.author.id != self.author.id:
                await interaction.response.send_message(
                    "` ❌ ` This isn't your panel.", ephemeral=True
                )
                return
        shift = config.get("shifts")
        permissions = shift.get("permissions")
        if not any(role.id in permissions for role in self.author.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        ShiftResult = await shifts.find_one(
            {"user": self.author.id, "status": {"$ne": "inactive"}}
        )
        if not ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` You don't have an active shift.", ephemeral=True
            )
            return
        await shifts.delete_one(
            {"_id": ShiftResult.get("_id")},
        )
        await interaction.response.send_message(
            "` ✅ ` Shift has been deleted.", ephemeral=True
        )


class RemoveTime(discord.ui.Modal):
    def __init__(self, author: discord.Member, shift: ObjectId):
        super().__init__(title="Remove Time")
        self.author = author
        self.shift = shift

    time = discord.ui.TextInput(
        label="Time (in minutes)",
        placeholder="Enter time in minutes",
        style=discord.TextStyle.short,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        shift = config.get("shifts")
        permissions = shift.get("permissions")
        if not any(role.id in permissions for role in self.author.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return
        try:
            time = int(self.time.value)
        except ValueError:
            await interaction.response.send_message(
                "` ❌ ` Please enter a valid number.", ephemeral=True
            )
            return
        if time <= 0:
            await interaction.response.send_message(
                "` ❌ ` Please enter a positive number.", ephemeral=True
            )
            return
        ShiftResult = await shifts.find_one({"_id": self.shift})
        if not ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` This shift doesn't exist.", ephemeral=True
            )
            return
        await shifts.update_one(
            {"_id": self.shift},
            {
                "$inc": {"duration": -time * 60},
            },
        )
        await interaction.response.edit_message(
            content=f"` ✅ ` Removed {time} seconds from the shift.",
            view=None,
            embed=None,
        )


class AddTime(discord.ui.Modal):
    def __init__(self, author: discord.Member, shift: ObjectId):
        super().__init__(title="Add Time")
        self.author = author
        self.shift = shift

    time = discord.ui.TextInput(
        label="Time (in minutes)",
        placeholder="Enter time in minutes",
        style=discord.TextStyle.short,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        shift = config.get("shifts")
        permissions = shift.get("permissions")
        if not any(role.id in permissions for role in self.author.roles):
            await interaction.response.send_message(
                f"` ❌ ` You don't have permission to run this command.", ephemeral=True
            )
            return

        try:
            time = int(self.time.value)

        except ValueError:
            await interaction.response.send_message(
                "` ❌ ` Please enter a valid number.", ephemeral=True
            )
            return
        if time <= 0:
            await interaction.response.send_message(
                "` ❌ ` Please enter a positive number.", ephemeral=True
            )
            return
        ShiftResult = await shifts.find_one({"_id": self.shift})
        if not ShiftResult:
            await interaction.response.send_message(
                "` ❌ ` This shift doesn't exist.", ephemeral=True
            )
            return
        await shifts.update_one(
            {"_id": self.shift},
            {
                "$inc": {"duration": time * 60},
            },
        )
        await interaction.response.send_message(
            content=f"` ✅ ` Added {time} seconds to the shift.", view=None, embed=None
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Shifts(client))
