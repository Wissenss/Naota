#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
import random
import discord
from discord.ext import commands

import connectionPool

import logging

from settings import *

from utils.variousUtils import getDiscordMainColor
from utils import playlistsUtils

import datetime

############ cogs ############
from cogs.musicPlayerCog import MusicPlayer
from cogs.watchlistCog import WatchlistCog
from cogs.devCog import DevCog
from cogs.chessCog import ChessCog
from cogs.twitterCog import TwitterCog
from cogs.competitiveProgrammingCog import CompetitiveProgramming
from cogs.achievementCog import AchievementCog
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
	await bot.add_cog(AchievementCog(bot))
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

	# then process all other commands
	await bot.process_commands(message)

@bot.hybrid_command(brief="create a poll", description="create a poll specifying <title> <option n> <option n + 1>...")
async def poll(ctx : commands.context, title : str, option_1 = "", option_2 = "", option_3 = "", option_4 = "", option_5 = "", option_6 = "", option_7 = "", option_8 = "", option_9 = "", option_10 = ""):
	LOGGER.log(logging.INFO, f"{ctx.command.qualified_name} called (USER ID {ctx.author.id}) (GUILD ID: {ctx.guild.id})")

  # fugly hack because slash commands don't support *args parameters
  # ----------------------------------------------------------------
	options = []

	if option_1 : options.append(option_1)
	if option_2 : options.append(option_2)
	if option_3 : options.append(option_3)
	if option_4 : options.append(option_3)
	if option_5 : options.append(option_3)
	if option_6 : options.append(option_3)
	if option_7 : options.append(option_3)
	if option_8 : options.append(option_3)
	if option_9 : options.append(option_3)
	if option_10 : options.append(option_3)
  # ----------------------------------------------------------------

	reactions = ["🍎", "🍊","🍇", "🥑", "🍞", "🧅", "🥚", "🌶️", "🥦", "🧀", "🥓", "🍓", "🫐", "🍿", "🍪", "🍭", "🍬"]

	em = discord.Embed(title=title, color=getDiscordMainColor())

	# maybe set the author to the one that send the message?
  # if utils.otherUtils.isAdmin(ctx) and is_official_poll:
  #   em.set_author(name="by Rooster Games")

	if len(options) == 0:
		message = await ctx.send(embed=em)
		
		await message.add_reaction("👍")
		await message.add_reaction("👎")

		return
	elif len(options) > 10:
		await ctx.send(f"define at most 10 options")
		return

	description_ = ""

	emojis = []

	for i, option in enumerate(options):
		emoji = reactions.pop(random.randint(0, len(reactions) - 1))
		
		emojis.append(emoji)

		description_ += f"\n{emoji} - {option}"

	em.description = description_

	message = await ctx.send(embed=em)

	for i in range(len(options)):
		await message.add_reaction(emojis[i])

@bot.hybrid_command(brief="ring the bell", description="that ain't like the visual novel your normie")
async def angrynoise(ctx : commands.context):
	LOGGER.log(logging.INFO, f"{ctx.command.qualified_name} called (USER ID {ctx.author.id}) (GUILD ID: {ctx.guild.id})")
	
	try:
		em = discord.Embed(color=getDiscordMainColor())
		
		LOGGER.log(logging.INFO, "  checking if user is connected to voice channel")
		# the user most be connected to a voice channel
		if not ctx.author.voice:
			em.description = "Connect to a voice channel"
			await ctx.send(embed=em)
			return
		
		voice_channel = ctx.voice_client

		disconect_after_play = False

		LOGGER.log(logging.INFO, "  trying to connect to voice channel")
		if not voice_channel:
			disconect_after_play = True
			voice_channel = await ctx.author.voice.channel.connect()

		ring_audio_path = ASSETS_DIRECTORY_PATH + "angry_noise.mp3"

		LOGGER.log(logging.INFO, f"  playing audio: {ring_audio_path}")

		audio = discord.FFmpegOpusAudio(source=ring_audio_path); 

		await voice_channel.play(audio)

		em.description = "🔔"	
		await ctx.send(embed=em)

		if disconect_after_play:
			LOGGER.log(logging.DEBUG, "  disconnecting from voice channel")
			await voice_channel.disconnect()

	except Exception as e:
		LOGGER.log(logging.INFO, f"unhandled exception: {repr(e)}")


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