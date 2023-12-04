import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

# import the diferent modules
from musicPlayer import MusicPlayer

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")

intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

guild_storage = {}

@bot.event
async def on_ready():
    await bot.add_cog(MusicPlayer())

@commands.command(brief="pong", description="test for correct bot connection")
async def ping(ctx):
	await ctx.send("pong")

bot.add_command(ping)

bot.run(BOT_TOKEN)