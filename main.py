import discord
from discord.ext import commands

import time
import os
import logging

import git

from settings import *

from variousUtils import getDiscordMainColor

############ cogs ############
from musicPlayer import MusicPlayer
# from competitiveProgramming import CompetitiveProgramming
##############################

intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents) #, application_id='1181086841445822474' this sould ve an environment variable! not in use for now, so I keep it commented...

@bot.event
async def on_ready():
	LOGGER.log(logging.INFO, "--------------------------- Initializing ---------------------------")
	LOGGER.log(logging.INFO, "loading cogs...")
	await bot.add_cog(MusicPlayer(bot))
	
	LOGGER.log(logging.INFO, "loading other commands...")
	bot.add_command(ping)
	bot.add_command(changelog)

	LOGGER.log(logging.INFO, "all set up!")
	LOGGER.log(logging.INFO, "--------------------------------------------------------------------")

@commands.command(brief="pong", description="test for correct bot connection")
async def ping(ctx):
	LOGGER.log(logging.INFO, f"ping called (Guild id: {ctx.guild.id})")
	
	await ctx.send("pong")
		 
@commands.command(brief="shows the most recent changes", description="get a list of all the recent improvements, new features and bug fixes done to naota")
async def changelog(ctx):
	LOGGER.log(logging.INFO, f"changelog called (Guild id: {ctx.guild.id})")

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

	em = discord.Embed(title=f"Naota v_{version}", description=logs, color=getDiscordMainColor())
	await ctx.send(embed=em)

bot.run(DISCORD_TOKEN)