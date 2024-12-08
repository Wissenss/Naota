#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
import discord
from discord.ext import commands

import connectionPool

import logging

from settings import *

from utils.variousUtils import getDiscordMainColor
from utils import playlistsUtils

import keyboard
import datetime

############ cogs ############
from cogs.musicPlayerCog import MusicPlayer
from cogs.watchlistCog import WatchlistCog
from cogs.devCog import DevCog
from cogs.chessCog import ChessCog
from cogs.twitterCog import TwitterCog
from cogs.competitiveProgrammingCog import CompetitiveProgramming
from cogs.achivementCog import AchivementCog
from cogs.keyboardCog import KeyboardCog
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
	#await bot.add_cog(WatchlistCog(bot))
	await bot.add_cog(DevCog(bot))
	await bot.add_cog(ChessCog(bot))
	await bot.add_cog(TwitterCog(bot))
	await bot.add_cog(AchivementCog(bot))
	await bot.add_cog(KeyboardCog(bot))
	#await bot.add_cog(CompetitiveProgramming(bot))
	
	LOGGER.log(logging.INFO, "loading other commands...")
	bot.help_command = CustomHelpCommand()

	LOGGER.log(logging.INFO, "starting connection pool...")
	connectionPool.init_connection_pool()

	LOGGER.log(logging.INFO, "all set up!")
	LOGGER.log(logging.INFO, "--------------------------------------------------------------------")

@bot.event
async def on_message(message : discord.Message):
	# { guild_id : music_channel_id } key value pairs
	music_channel_id = playlistsUtils.get_guild_music_channel_id(message.guild)

	print(f"music_channel_id: {music_channel_id}")

	if message.channel.id == music_channel_id:
		conn = connectionPool.get_connection()
		curs = conn.cursor()

		url = playlistsUtils.get_youtube_url_from_message(message)

		if not url:
			return

		LOGGER.log(logging.DEBUG, f"apending url: {url} to default playlist for guild: {message.guild.id}")

		default_playlist_id = playlistsUtils.get_default_playlist_id(message.guild)

		sql = "INSERT INTO playlist_items(url, playlist_id) VALUES(?, ?);"

		curs.execute(sql, [url, default_playlist_id])

		conn.commit()

		connectionPool.release_connection(conn)

# @bot.hybrid_command(name="about", hidden=True)
# async def About(ctx):
# 	em = discord.Embed(title="", description="", color=getDiscordMainColor())
# 	await ctx.send(embed=em)

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