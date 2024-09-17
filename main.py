import discord
import sys

sys.dont_write_bytecode = True
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import time
import platform

load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")


class client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX), intents=intents
        )
        self.client = client
        self.cogslist = [
            "Modules.moderations",
            "Events.on_moderation",
            "Events.on_moderation_edit",
            "Events.on_shift_start",
            "Events.on_shift_end",
            "Events.on_shift_break",
            "Events.on_shift_resume",
            "Modules.shifts",
            "Modules.absenses",
            "Events.on_loa_end"
        ]

    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension("jishaku")

    async def on_ready(self):
        prfx = time.strftime("%H:%M:%S GMT", time.gmtime())
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " + discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + str(len(synced)) + " Commands")
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")

    async def setup_hook(self):
        self.loop.create_task(self.load_jishaku())

        for ext in self.cogslist:
            await self.load_extension(ext)
            print(f"{ext} loaded")


Client = client()
Client.run(TOKEN)
