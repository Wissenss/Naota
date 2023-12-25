import discord
from discord.ext import commands

import time
import os
from dotenv import load_dotenv

import git

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
	
	bot.add_command(ping)
	bot.add_command(changelog)

@commands.command(brief="pong", description="test for correct bot connection")
async def ping(ctx):
	await ctx.send("pong")
		 
@commands.command(brief="shows the most recent changes", description="get a list of all the recent improvements, new features and bug fixes done to naota")
async def changelog(ctx):
	# obtain the log from local repo
	repo = git.Repo(os.getcwd())

	commit_list = list(repo.iter_commits(all=True))

	# number of commits = version number
	version = f"0.0.{len(commit_list)}"
	
	# show the last 5 commits messages
	logs = ""

	for i in range(5):
		commit = commit_list[i]

		date = time.gmtime(commit.committed_date)
		author = commit.author
		message = commit.message

		logs += f"[{date.tm_year}/{date.tm_mon}/{date.tm_mday}] - {message}\n"

	em = discord.Embed(title=f"Naota v_{version}", description=logs, color=discord.Color.dark_blue())
	await ctx.send(embed=em)

bot.run(DISCORD_TOKEN)