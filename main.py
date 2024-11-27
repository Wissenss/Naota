#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
import discord
from discord.ext import commands

import connectionPool

import logging

from settings import *

from utils.variousUtils import getDiscordMainColor

import keyboard
import datetime

############ cogs ############
from cogs.musicPlayerCog import MusicPlayer
from cogs.watchlistCog import WatchlistCog
from cogs.devCog import DevCog
from cogs.chessCog import ChessCog
from cogs.twitterCog import TwitterCog
from cogs.competitiveProgrammingCog import CompetitiveProgramming
##############################

from commands.helpCommand import *

intents =  discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

pause_command_timeout = datetime.datetime.now()

@bot.event
async def on_ready():
	pass

@bot.event
async def setup_hook():
	LOGGER.log(logging.INFO, "--------------------------- Initializing ---------------------------")

	LOGGER.log(logging.INFO, "loading cogs...")
	await bot.add_cog(MusicPlayer(bot))
	await bot.add_cog(WatchlistCog(bot))
	await bot.add_cog(DevCog(bot))
	await bot.add_cog(ChessCog(bot))
	await bot.add_cog(TwitterCog(bot))
	#await bot.add_cog(CompetitiveProgramming(bot))
	
	LOGGER.log(logging.INFO, "loading other commands...")
	bot.help_command = CustomHelpCommand()

	LOGGER.log(logging.INFO, "starting connection pool...")
	connectionPool.init_connection_pool()

	LOGGER.log(logging.INFO, "all set up!")
	LOGGER.log(logging.INFO, "--------------------------------------------------------------------")

# @bot.hybrid_command(name="about", hidden=True)
# async def About(ctx):
# 	em = discord.Embed(title="", description="", color=getDiscordMainColor())



# 	await ctx.send(embed=em)

# must check how to raise key presses on main session
# @bot.hybrid_command(name="allow", brief="allow certain action", hidden=True)
# async def Allow(ctx, action : str):
# 	if not permissionsUtils.command_allowed_in_context(ctx, ctx.command):
# 		return

# 	action = action.lower()

# 	em = discord.Embed(description="", color=getDiscordMainColor())

# 	if action == "space":
# 		global pause_command_timeout
# 		pause_command_timeout = datetime.datetime.now() + datetime.timedelta(days=0, hours=2)

# 		em.description = f"timeout for !space command set to 2 hours from now"
# 		await ctx.send(embed=em)
# 		return

# 	em = discord.Embed(description=f"action {action} not recognized", color=discord.Color.red())
# 	await ctx.send(embed=em)

# @bot.hybrid_command(name="space", brief="press the space bar", description="allow you to remotely press the space bar")
# async def pressSpace(ctx):
# 	global pause_command_timeout

# 	if datetime.datetime.now() > pause_command_timeout:
# 		em = discord.Embed(description="permission for !space command not granted", color=discord.Color.red())
# 		await ctx.send(embed=em)
# 		return
	
# 	em = discord.Embed(description="pressing space...", color=getDiscordMainColor())
# 	await ctx.send(embed=em)
# 	keyboard.press_and_release("space")

@bot.tree.command(name="help")
async def CustomHelpSlashCommand(interaction : discord.Interaction, resource : str = None):
	em = None

	# [TODO] handle resource not found exception

	ctx = await commands.Context.from_interaction(interaction)

	if resource == None:
		# Retrieve the bot mapping. this is basically a copy of the method behaviour inside HelpCommand class
		mapping: Dict[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]] = {cog: cog.get_commands() for cog in bot.cogs.values()}
		mapping[None] = [c for c in bot.commands if c.cog is None]

		em = get_help_embed(ctx, mapping)
		await interaction.response.send_message(embed=em)
		return

	cog = bot.get_cog(resource)
	if cog != None:
		em = get_cog_help_embed(cog, ctx)
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