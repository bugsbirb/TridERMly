from __future__ import annotations

import discord
from discord.ext import commands


class Simple(discord.ui.View):

    def __init__(
        self,
        *,
        timeout: int = 60,
        PreviousButton: discord.ui.Button = discord.ui.Button(emoji="<"),
        NextButton: discord.ui.Button = discord.ui.Button(emoji=">"),
        FirstEmbedButton: discord.ui.Button = discord.ui.Button(emoji="<<"),
        LastEmbedButton: discord.ui.Button = discord.ui.Button(emoji=">>"),
        PageCounterStyle: discord.ButtonStyle = discord.ButtonStyle.grey,
        InitialPage: int = 0,
        ephemeral: bool = False,
    ) -> None:
        self.PreviousButton = PreviousButton
        self.FirstEmbedButton = FirstEmbedButton
        self.LastEmbedButton = LastEmbedButton
        self.NextButton = NextButton
        self.PageCounterStyle = PageCounterStyle
        self.InitialPage = InitialPage
        self.ephemeral = ephemeral

        self.pages = None
        self.ctx = None
        self.message = None
        self.current_page = None
        self.page_counter = None
        self.total_page_count = None

        super().__init__(timeout=timeout)

    async def start(
        self,
        ctx: discord.Interaction | commands.Context,
        pages: list[discord.Embed]
    ):
        if isinstance(ctx, discord.Interaction):
            ctx = await commands.Context.from_interaction(ctx)

        self.pages = pages
        self.total_page_count = len(pages)
        self.ctx = ctx
        self.current_page = self.InitialPage

        self.PreviousButton.callback = self.previous_button_callback
        self.NextButton.callback = self.next_button_callback
        self.FirstEmbedButton.callback = self.start_button_callback  #
        self.LastEmbedButton.callback = self.end_button_callback

        self.page_counter = SimplePaginatorPageCounter(
            style=self.PageCounterStyle,
            TotalPages=self.total_page_count,
            InitialPage=self.InitialPage,
        )
        self.add_item(self.FirstEmbedButton)
        self.add_item(self.PreviousButton)
        self.add_item(self.page_counter)
        self.add_item(self.NextButton)
        self.add_item(self.LastEmbedButton)

        self.message = await ctx.send(
            content="", embed=self.pages[self.InitialPage], view=self
        )

    async def previous(self):
        if self.current_page == 0:
            self.current_page = self.total_page_count - 1
        else:
            self.current_page -= 1

        self.page_counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await self.message.edit(embed=self.pages[self.current_page], view=self)

    async def next(self):
        if self.current_page == self.total_page_count - 1:
            self.current_page = 0
        else:
            self.current_page += 1

        self.page_counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await self.message.edit(embed=self.pages[self.current_page], view=self)

    async def next_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.next()
        await interaction.response.defer()

    async def previous_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.previous()
        await interaction.response.defer()

    async def start_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.current_page = 0
        self.page_counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await self.message.edit(embed=self.pages[self.current_page], view=self)
        await interaction.response.defer()

    async def end_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            embed = discord.Embed(
                description=f"**{interaction.user.display_name},** this is not your panel!",
                color=discord.Colour.brand_red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.current_page = self.total_page_count - 1
        self.page_counter.label = f"{self.current_page + 1}/{self.total_page_count}"
        await self.message.edit(embed=self.pages[self.current_page], view=self)
        await interaction.response.defer()


class SimplePaginatorPageCounter(discord.ui.Button):
    def __init__(self, style: discord.ButtonStyle, TotalPages, InitialPage):
        super().__init__(
            label=f"{InitialPage + 1}/{TotalPages}", style=style, disabled=True
        )
