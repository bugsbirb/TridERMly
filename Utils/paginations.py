import discord
from Utils.Roblox import RobloxThumbnail

class ActivePagination(discord.ui.View):
    def __init__(self, author: discord.Member, ActiveStaff):
        super().__init__()
        self.page = 1
        self.author = author
        self.TotalPages = (len(ActiveStaff) + 29) // 30
        self.ActiveStaff = ActiveStaff

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.page > 1:
            self.page -= 1
            self.next.disabled = False
            button.disabled = self.page == 1
            await self.UpdateActive(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple, disabled=True)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.TotalPages:
            self.page += 1
            self.previous.disabled = False
            button.disabled = self.page == self.TotalPages
            await self.UpdateActive(interaction)

    async def UpdateActive(self, interaction: discord.Interaction):
        Start = (self.page - 1) * 30
        End = Start + 30

        StaffMembers = list(self.ActiveStaff.keys())[Start:End]

        if StaffMembers:
            description = ""
            for i, MemberID in enumerate(StaffMembers, start=Start + 1)[:30]:
                ShiftResult = self.ActiveStaff.get(MemberID)
                if ShiftResult:
                    description += (
                        f"> **<@{MemberID}>** • <t:{int(ShiftResult.get('start'))}:R>\n"
                    )

            self.TotalPages = (len(self.ActiveStaff) + 29) // 30
        else:
            description = "No active shifts to display."

        self.next.disabled = self.page >= self.TotalPages
        self.previous.disabled = self.page <= 1
        embed = discord.Embed(
            title="Active Shifts",
            color=discord.Color.dark_embed(),
            description=description,
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)

        await interaction.response.edit_message(embed=embed, view=self)


class LeaderboardPagination(discord.ui.View):
    def __init__(
        self, author: discord.Member, durations: dict, members: list, PageSize: int
    ):
        super().__init__()
        self.page = 1
        self.author = author
        self.durations = durations
        self.members = members
        self.PageSize = PageSize
        self.TotalPages = (len(members) + PageSize - 1) // PageSize

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.page > 1:
            self.page -= 1
            self.next.disabled = False
            button.disabled = self.page == 1
            await self.update(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple, disabled=True)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.TotalPages:
            self.page += 1
            self.previous.disabled = False
            button.disabled = self.page == self.TotalPages
            await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        start = (self.page - 1) * self.PageSize
        end = start + self.PageSize
        page_members = self.members[start:end]

        description = ""
        for i, member in enumerate(page_members, start=start + 1):
            duration = self.durations.get(member.id, 0)
            total_hours, remainder = divmod(duration, 3600)
            total_minutes, total_seconds = divmod(remainder, 60)

            Time = (
                f"{int(total_hours)}h " * (total_hours > 0)
                + f"{int(total_minutes)}m " * (total_minutes > 0)
                + f"{int(total_seconds)}s"
            ).strip()

            description += f"**{i}.** {member.mention} • {Time}\n"

        embed = discord.Embed(
            title="Shift Leaderboard",
            color=discord.Color.dark_embed(),
            description=description,
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)

        self.next.disabled = self.page >= self.TotalPages
        self.previous.disabled = self.page <= 1
        await interaction.response.edit_message(embed=embed, view=self)
class PunishmentPagination(discord.ui.View):
    def __init__(self, author, moderation):
        super().__init__()
        self.author = author
        self.moderation = moderation
        self.Current = 0
        self.UpdateButtons()

    def UpdateButtons(self):
        self.previous.disabled = self.Current == 0
        self.next.disabled = (self.Current + 1) * 10 >= len(self.moderation)

    async def update(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.clear_fields()

        Start = self.Current * 10
        End = Start + 10
        for i, mod in enumerate(self.moderation[Start:End]):
            embed.add_field(
                name=f"`{mod.get('_id')}`",
                value=f"> **Issuer:** <@{mod.get('author')}>\n"
                f"> **Action:** {mod.get('action')}\n"
                f"> **Reason:** {mod.get('reason')}\n"
                f"> **Jump:** {mod.get('jump')}",
                inline=False,
            )

        embed.title = f"Punishments for @{self.moderation[0].get('username')}"
        embed.set_author(
            name=f"@{self.moderation[0].get('username')}",
            icon_url=await RobloxThumbnail(self.moderation[0].get("UserID")),
        )
        embed.set_thumbnail(url=await RobloxThumbnail(self.moderation[0].get("UserID")))

        self.UpdateButtons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.Current > 0:
            self.Current -= 1
            await self.update(interaction)
        else:
            button.disabled = True
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.Current + 1) * 10 < len(self.moderation):
            self.Current += 1
            await self.update(interaction)
        else:
            button.disabled = True
            await interaction.response.edit_message(view=self)