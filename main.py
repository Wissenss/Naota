import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

# import the diferent modules
from musicPlayer import MusicPlayer
# from competitiveProgramming import CompetitiveProgramming

load_dotenv(override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX")

intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, application_id='1181086841445822474')

@bot.event
async def on_ready():
	# print("online")
	# print("loading cogs...")
	
	# await bot.load_extension("musicPlayer")
	
	# print("finished")
  await bot.add_cog(MusicPlayer(bot))
  # await bot.add_cog(CompetitiveProgramming())
  # synced = await bot.tree.sync() #guild=[discord.abc.Snowflake(id=1178465444701687878)]
  # print(f"syced: {len(synced)}")

@commands.command(brief="pong", description="test for correct bot connection")
async def ping(ctx):
	await ctx.send("pong")

bot.add_command(ping)

bot.run(DISCORD_TOKEN)