from typing import Any, Dict, List, Optional
import discord
from discord.ext import commands

import time
import os
import logging

import git

import sqlite3

from settings import *

from utils.variousUtils import getDiscordMainColor

############ cogs ############
#from musicPlayer import MusicPlayer
from cogs.musicPlayerCogV2 import MusicPlayer
from cogs.kuvaCog import KuvaCog 
from cogs.chemsCog import ChemsCog
##############################

from commands.helpCommand import *

intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
	pass

@bot.event
async def setup_hook():
	LOGGER.log(logging.INFO, "--------------------------- Initializing ---------------------------")
	# LOGGER.log(logging.INFO, "connecting to database...")
	# DB_CONNECTION = sqlite3.connect(DB_FILE_PATH)

	LOGGER.log(logging.INFO, "loading cogs...")
	await bot.add_cog(MusicPlayer(bot))
	# await bot.add_cog(KuvaCog(bot))
	await bot.add_cog(ChemsCog(bot))
	
	LOGGER.log(logging.INFO, "loading other commands...")
	bot.add_command(ping)
	bot.add_command(changelog)
	bot.add_command(sync)

	bot.help_command = CustomHelpCommand()

	LOGGER.log(logging.INFO, "all set up!")
	LOGGER.log(logging.INFO, "--------------------------------------------------------------------")

@commands.command(brief="pong", description="test for correct bot connection")
async def ping(ctx):
	LOGGER.log(logging.INFO, f"ping called (Guild ID: {ctx.guild.id})")
	
	await ctx.send("pong")

@commands.command(brief="shows the most recent changes", description="get a list of all the recent improvements, new features and bug fixes done to naota")
async def changelog(ctx):
	LOGGER.log(logging.INFO, f"changelog called (Guild ID: {ctx.guild.id})")

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

@commands.command(hidden=True)
async def sync(ctx):
	LOGGER.log(logging.INFO, f"sync called (Guild ID: {ctx.guild.id})")

	await bot.tree.sync()

	em = discord.Embed(description="syncing commands", color=getDiscordMainColor())

	await ctx.send(embed=em)

@bot.tree.command(name="help")
async def CustomHelpSlashCommand(interaction : discord.Interaction, resource : str = None):
	em = None

	# [TODO] handle resource not found exception

	if resource == None:
		# Retrieve the bot mapping. this is basically a copy of the method behaviour inside HelpCommand class
		mapping: Dict[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]] = {cog: cog.get_commands() for cog in bot.cogs.values()}
		mapping[None] = [c for c in bot.commands if c.cog is None]

		em = get_help_embed(interaction.context, mapping)
		await interaction.response.send_message(embed=em)
		return

	cog = bot.get_cog(resource)
	if cog != None:
		em = get_cog_help_embed(cog)
		await interaction.response.send_message(embed=em)
		return

	maybe_coro = discord.utils.maybe_coroutine

	# If it's not a cog then it's a command.
	# Since we want to have detailed errors when someone
	# passes an invalid subcommand, we need to walk through
	# the command group chain ourselves.
	keys = resource.split(' ')
	cmd = bot.all_commands.get(keys[0])
	if cmd is None:
		# string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
		# return await self.send_error_message(string)
		return

	for key in keys[1:]:
			try:
				found = cmd.all_commands.get(key)  # type: ignore
			except AttributeError:
				# string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
				# return await self.send_error_message(string)
				return
			else:

				if found is None:
					# string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
					# return await self.send_error_message(string)
					return
				
				cmd = found				

	if isinstance(cmd, commands.Group):
		em = get_group_help_embed(cmd)
		await interaction.response.send_message(embed=em)
		return
	else:
		em = get_command_help_embed(cmd)
		await interaction.response.send_message(embed=em)
		return 

	# command = bot.get_command(resource)

	# if isinstance(command, commands.Command):
	# 	em = helpCommand.get_group_help_embed(command)
	# 	await interaction.response.send_message(embed=em)
	# 	return

	# if isinstance(command, commands.Group):
	# 	em = helpCommand.get_command_help_embed(command)
	# 	await interaction.response.send_message(embed=em)
	# 	return

bot.run(DISCORD_TOKEN)