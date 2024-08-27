import os
import logging
import time
import datetime
import asyncio
from typing import List
import uuid
import random
import subprocess

import discord
from discord.ext import tasks, commands

import yt_dlp
from googleapiclient.discovery import build

from settings import LOGGER, LOG_LEVEL, YOUTUBE_TOKEN, DB_CONNECTION
from utils.variousUtils import getDiscordMainColor
from utils import permissionsUtils

from sentiment.sentiment_analysis import process_youtube_comments

# this class should not be instantiated from outside the AudioPlaylist items
class AudioPlaylistItem:
  def __init__(self):
    self.row_id = -1
    self.original_url : str = ""
    self.title : str = ""
    self.origin_id : int = 0
    self.playlist_row_id : int = -1
  
  def __init__(self, row_id : int):
    cursor = DB_CONNECTION.cursor()

    sql = "SELECT * FROM playlist_items WHERE rowId = ?;"

    cursor.execute(sql, [row_id])

    item = cursor.fetchone()

    self.row_id = item[0]
    self.original_url = item[1]
    self.title = item[2]
    self.origin_id = item[3]
    self.playlist_row_id = item[4]

    cursor.close()

  def load_data(self, data):
    self.title = data["title"]
    self.original_url = data["original_url"]
    self.is_live = data["is_live"]
    self.thumbnail = data["thumbnail"]
    self.id = data["id"]

class AudioPlaylist:
  def __init__(self):
    self.rowId : int = -1
    self.name : str = ""
    self.owner_user_id : int = 0

    self.item_count = 0
    self.items : list[AudioPlaylistItem] = []

  def __init__(self, index : int, owner_user_id : int):
    print("constructor 2 called")

    try:
      # get rowid out of the order by rowid base index
      cursor =  DB_CONNECTION.cursor()

      sql = "SELECT * FROM playlists WHERE ownerUserId = ? ORDER BY rowId;"
      
      cursor.execute(sql, [owner_user_id])

      raw_playlists_rows = cursor.fetchall()

      if (index < 0 or index >= len(raw_playlists_rows)):
        raise IndexError("the given playlist index value does not exists on the db")

      raw_playlist = raw_playlists_rows[index]

      self.load_data_from_row_id(raw_playlist[0])

    except Exception as e:
      if DB_CONNECTION.in_transaction:
        DB_CONNECTION.rollback()

      LOGGER.log(logging.ERROR, f"Exception on playlist_show command:\n{repr(e)}")

    finally:
      cursor.close()

  def load_data_from_row_id(self, row_id):
    print("load_data_from_row_id called")
    # get the playlist info
    cursor =  DB_CONNECTION.cursor()
    
    sql = "SELECT * FROM playlists WHERE rowId = ?"

    cursor.execute(sql, [row_id])

    raw_playlist = cursor.fetchone()

    self.rowId = raw_playlist[0]
    self.owner_user_id = raw_playlist[1]
    self.name = raw_playlist[2]

    # get the songs of the playlist
    sql = "SELECT rowId FROM playlist_items WHERE playlistRowId = ?"

    cursor.execute(sql, [self.rowId])

    raw_playlist_items = cursor.fetchall()

    self.items : list[AudioPlaylistItem] = []
    self.item_count = 0

    for raw_item in raw_playlist_items:
      item = AudioPlaylist(raw_item[0])

      self.items.append(item)
      self.item_count += 1

  def new_item(self) -> AudioPlaylistItem:
    item : AudioPlaylist = AudioPlaylistItem()

    item.playlist_row_id = self.row_id

    return item

  def add(self, item : AudioPlaylistItem):
    try:
      cursor = DB_CONNECTION.cursor()

      sql = "INSERT INTO playlist_items(originalUrl, title, originId, playlistRowId) VALUES(?, ?, ?, ?);"

      cursor.execute(sql, [item.original_url, item.title, item.origin_id, self.rowId])

      DB_CONNECTION.commit()

      self.items.append(item)

      self.item_count += 1

    except:
      if DB_CONNECTION.in_transaction:
        DB_CONNECTION.rollback()

    finally:
      cursor.close()

  def remove(self, index : int) -> AudioPlaylistItem:
    if (index > len(self.items) - 1):
      raise IndexError()
    
    item = self.items[index]

    try:
      cursor = DB_CONNECTION.cursor()
      
      sql = "DELETE FROM playlist_items WHERE rowid = ?;"

      cursor.execute(sql, [item.row_id])

      DB_CONNECTION.commit()

    except:
      if DB_CONNECTION.in_transaction:
        DB_CONNECTION.rollback()

    finally:
      cursor.close()

    self.items.pop(index)
    self.item_count -= 1

    return item

class AudioResource:
  def __init__(self):
    self.original_url : str = ""
    self.url : str = "" # this is the manifests streaming url
    self.uuid : uuid.UUID = uuid.uuid4()

    self.source : discord.AudioSource = None

    # youtube data
    self.id : str = ""
    self.title : str = ""
    self.thumbnail : str = "" 
    self.is_live : bool = False
    self.duration : float = datetime.timedelta(0, 0, 0, 0).total_seconds()

  def load_data(self, data : dict):
    self.original_url : str = data["original_url"]
    self.id : str = data["id"]
    self.title : str = data["title"]
    self.thumbnail : str = data["thumbnail"]
    self.is_live : bool = data["is_live"]

    if self.is_live:
      self.url : str = data["url"]

      self.source : discord.AudioSource = discord.FFmpegOpusAudio(self.url)
    else:
      duration_string = data["duration_string"]

      # [TODO] handle other formats, for example if the video is xDays yHours this will break...

      t = datetime.datetime.strptime(duration_string, "%M:%S")
      delta = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)

      self.duration = delta.total_seconds()


class AudioBuffer:
  __buffer_path = ".\\buffer"

  @staticmethod
  def get_file_path(resource : AudioResource):
    filepath = os.path.join(AudioBuffer.__buffer_path, f"{str(resource.uuid)}.mp3")
    return filepath

  @staticmethod
  def exists(resource : AudioResource):
    filename = f"{str(resource.uuid)}.mp3"
    return AudioBuffer.exists_filename(filename)

  @staticmethod 
  def exists_filename(filename : str):
    filepath = os.path.join(AudioBuffer.__buffer_path, filename)
    return AudioBuffer.exists_filepath(filepath)

  @staticmethod
  def exists_filepath(filepath : str):
    return os.path.isfile(filepath)

  @staticmethod
  def remove(resource : AudioResource):
    filename = f"{str(resource.uuid)}.mp3"
    AudioBuffer.remove_filename(filename)

    filename_org = f"{str(resource.uuid)}_origianl.mp3"
    if AudioBuffer.exists_filename(filename_org):
      AudioBuffer.remove_filename(filename_org)
    
  @staticmethod
  def remove_filename(filename : str):
    filepath = os.path.join(AudioBuffer.__buffer_path, filename)
    AudioBuffer.remove_filepath(filepath)

  @staticmethod
  def remove_filepath(filepath : str):
    os.remove(filepath)

  @staticmethod
  def purge(): # this will clean all files in buffer that are older than an hour
    for filename in os.listdir(AudioBuffer.__buffer_path):
      filepath = os.path.join(AudioBuffer.__buffer_path, filename) 
      
      current_time = time.time()
      modify_time = os.path.getctime(filepath)

      if (current_time - modify_time > 60 * 60):
        os.remove(filepath)

  @staticmethod
  async def add(audio : AudioResource):
    return await AudioBuffer.__add(audio.original_url, audio.uuid)

  @staticmethod
  async def __add(youtube_url : str, uuid):
    outtmpl = f"{AudioBuffer.__buffer_path}/{str(uuid)}.mp3"

    ytdlopts = {
      'format': 'bestaudio/best',
      'outtmpl': outtmpl,
      'restrictfilenames': True,
      'noplaylist': True,
      'nocheckcertificate': True,
      'ignoreerrors': False,
      'logtostderr': False,
      'quiet': True,
      "external_downloader_args": ['-loglevel', 'panic'],
      'no_warnings': True,
      'default_search': 'auto',
      'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
    }

    ytdl = yt_dlp.YoutubeDL(ytdlopts)

    data = ytdl.extract_info(youtube_url, download=True)

    return (data, outtmpl)


class AudioQueue:
  def __init__(self):
    self.__queue : list[AudioResource] = []

    self.downloader = tasks.loop(seconds=1)(self.__download_task)

    self.downloader.start()

  def append_resource(self, audio : AudioResource):
    self.__queue.append(audio)

  def append(self, url : str):
    resource = AudioResource()

    resource.original_url = url

    self.__queue.append_resource(resource)

  def pop(self, index : int = 0, deleteFile : bool = True):
    resource = self.__queue[index]

    if AudioBuffer.exists(resource) and deleteFile:
      AudioBuffer.remove(resource)

    return self.__queue.pop(index)

  def get(self, index):
    return self.__queue[index]

  def count(self):
    return len(self.__queue)

  def clear(self):
    for resource in self.__queue:
      if AudioBuffer.exists(resource):
        AudioBuffer.remove(resource)

    self.__queue.clear()
    return 

  def shuffle(self):
    return random.shuffle(self.__queue)

  async def __download_task(self):
    audio : AudioResource
    for i, audio in enumerate(self.__queue):
      if i > 10 or audio.is_live == True:
        return
      
      if AudioBuffer.exists(audio) == False:
        # print(audio.url) # for debug

        video_data, filePath = await AudioBuffer.add(audio)

        # for d in video_data: # for debug
        #   print(f"{d}: {video_data[d]}")

        audio.load_data(video_data)
        audio.source = discord.FFmpegOpusAudio(filePath)


class AudioQueuesHandler:
  __Queues_pool = {}

  @staticmethod
  def get_queue(guild_id : int):
    if not guild_id in AudioQueuesHandler.__Queues_pool.keys():
      AudioQueuesHandler.__Queues_pool[guild_id] = AudioQueue()

    return AudioQueuesHandler.__Queues_pool[guild_id]


class AudioStream:
  def __init__(self, guild_id : int, bot : commands.bot):
    self.bot = bot

    # maybe here w'll need an AudioStream UUID, for logging porpuses mainly

    self.guild_id : int = guild_id
    self.voice_channel : discord.VoiceClient = None
    self.audio : AudioResource = None

    self.queue : AudioQueue = AudioQueuesHandler.get_queue(guild_id)

    self._stream_task = tasks.loop(seconds=1)(self.__stream_task)

    # internal workflow flags
    self.is_changing_speed = False

  def start_stream(self, voice_channel : discord.VoiceClient):
    if self._stream_task.is_running():
      raise Exception("Stream is already running!")

    self.voice_channel = voice_channel

    self._stream_task.start()

  async def stop_stream(self):
    await self.voice_channel.disconnect()

    self._stream_task.cancel()
    self.queue.clear()
    self.audio = None
    
    #await self.voice_channel.disconnect()

  def pause_stream(self):
    self.voice_channel.pause()

  def resume_stream(self):
    self.voice_channel.resume()

  def skip_stream(self):
    return self.voice_channel.stop()

  def is_paused(self):
    return self.voice_channel.is_paused()

  def is_running(self) -> bool:
    return self._stream_task.is_running()

  def set_speed(self, speed : float):
    print(f"changing speed x{speed}")
    self.is_changing_speed = True

    if self.voice_channel.is_playing():
      self.voice_channel.stop()

    if AudioBuffer.exists(self.audio):
      self.audio.source.cleanup()
      filename     = f"{str(self.audio.uuid)}.mp3"
      filepath     = AudioBuffer.get_file_path(self.audio)
      filename_org = f"{str(self.audio.uuid)}_original.mp3"
      filepath_org = os.path.join(AudioBuffer._AudioBuffer__buffer_path, filename_org)

      if not AudioBuffer.exists_filename(filename_org):
        os.rename(filepath, filepath_org)
      else:
        AudioBuffer.remove_filename(filename)

      ffmpeg_cmd = [
        "ffmpeg",
        "-i", filepath_org,
        "-filter:a", f"atempo={speed}",
        filepath
      ]

      subprocess.run(ffmpeg_cmd)

      self.audio.source = discord.FFmpegOpusAudio(filepath)
      self.voice_channel.play(self.audio.source)

    self.is_changing_speed = False
    print(f"changing speed finished")

  async def __stream_task(self): # this is a loop, think of it as such: once the start_stream function is called this will run every second
    if self.voice_channel == None:
      return

    # disconnect and stop if no member on channel. it has a 5 second tolerance
    # print(f"members on channel: {len(self.voice_channel.channel.members)}") # for debug
    if len(self.voice_channel.channel.members) <= 1:
      await asyncio.sleep(5)
      if len(self.voice_channel.channel.members) <= 1:
        LOGGER.log(logging.INFO, f"stoping stream: no member on voice channel")
        await self.stop_stream()
        return
    
    if self.is_changing_speed:
      return

    if self.voice_channel.is_paused():
      return

    if self.voice_channel.is_playing():
      return

    # if not playing and audio is not none, this means the song just ended, so we can delete the .mp3 file if any
    elif self.audio != None and self.is_changing_speed == False:
      print("song ended, deletin file...")
      if AudioBuffer.exists(self.audio):
        AudioBuffer.remove(self.audio)

    if self.queue.count() == 0:
      LOGGER.log(logging.INFO, f"stoping stream: no songs on queue")
      await self.stop_stream()
      return

    self.audio : AudioResource = self.queue.get(0)

    if self.audio.source == None: 
      await asyncio.sleep(3)

    self.voice_channel.play(self.audio.source)

    self.queue.pop(0, False)


class AudioStreamsHandler:
  __Streams_pool = {}

  @staticmethod
  def get_stream(guild_id : int, bot : commands.Bot) -> AudioStream :
    if not guild_id in AudioStreamsHandler.__Streams_pool.keys():
      AudioStreamsHandler.__Streams_pool[guild_id] = AudioStream(guild_id, bot)

    return AudioStreamsHandler.__Streams_pool[guild_id]


class MusicPlayer(commands.Cog):
  "A music player for youtube"

  def __init__(self, bot : commands.bot):
    self.bot = bot
    self.constant_buffer_purge.start()

  @tasks.loop(minutes=60)
  async def constant_buffer_purge(self):
    AudioBuffer.purge()

  async def cog_before_invoke(self, ctx : commands.Context):
    LOGGER.log(logging.INFO, f"{ctx.command.name} called (USER ID: {ctx.author.id}) (GUILD ID: {ctx.guild.id})")

  async def cog_check(self, ctx):
    return permissionsUtils.cog_allowed_in_context(ctx, self)

  async def cog_after_invoke(self, ctx: commands.Context):
    pass

  async def __play_url(self, ctx : commands.Context, url : str):

    em = discord.Embed(color=getDiscordMainColor())

    # the user most be connected to a voice channel
    if not ctx.author.voice:
      em.description = "Connect to a voice channel"
      await ctx.send(embed=em)
      return

    # we respond to interaction so it doesn't times out
    em.description = f"Quering **[URL]({url})** resources"
    msg : discord.Message = await ctx.send(embed=em)

    # the url most be a valid youtube link
    try:
      ytdlopts = {
      'format': 'bestaudio/best',
      'restrictfilenames': True,
      'noplaylist': True,
      'nocheckcertificate': True,
      'ignoreerrors': False,
      'logtostderr': False,
      'quiet': True,
      "external_downloader_args": ['-loglevel', 'panic'],
      'no_warnings': True,
      'default_search': 'auto',
      'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
    }

      ytdl = yt_dlp.YoutubeDL(ytdlopts)
      data = ytdl.extract_info(url=url, download=False)
      audio = AudioResource()
      audio.load_data(data)

      if LOG_LEVEL == "DEBUG":
        for d in data: # for debug
          LOGGER.log(logging.DEBUG, f"{d}: {data[d]}")

    except Exception as e:
      LOGGER.log(logging.DEBUG, f"{repr(e)}")
      em.description = "Invalid url"
      await msg.edit(embed=em)
      return

    # the videos should not be longer than 15 minutes
    if not audio.is_live:
      if audio.duration > datetime.timedelta(hours=0, minutes=15, seconds=0).total_seconds():
        em.description = "Video too long"
        await msg.edit(embed=em)
        return

    voice_channel = ctx.guild.voice_client

    if not voice_channel:
      voice_channel = await ctx.author.voice.channel.connect()

    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)
    audio_stream.queue.append_resource(audio)

    em.description = f"**Appending** **[{audio.title}]({audio.original_url})**"

    if not audio_stream.is_running():
      audio_stream.start_stream(voice_channel)
      em.description = f"**Playing** **[{audio.title}]({audio.original_url})**"

    em.set_image(url=audio.thumbnail)

    # 9: !play url / !play search show "(live)" tag if resource is a live stream
    if (audio.is_live == True):
      em.description += " (live)"

    await msg.edit(embed=em)
    return

  @commands.hybrid_group(brief="play some music", description="stream the given <url> audio to voice channel. The <url> has to be a valid youtube link")
  async def play(self, ctx : commands.Context, url : str):
    return await self.__play_url(ctx, url)

  @play.command(name="url", brief="play some music", description="stream the given <url> audio to voice channel. The <url> has to be a valid youtube link")
  async def play_url(self, ctx : commands.Context, url : str):
    return await self.__play_url(ctx, url)

  @play.command(name="search", brief="search and play music", description="stream the query result of a youtube search to voice channel")
  async def play_search(self, ctx : commands.Context, query : str):
    youtube = build("youtube", "v3" , developerKey=YOUTUBE_TOKEN)

    request = youtube.search().list(part="snippet", q=query)

    response = request.execute()

    results_list = response["items"]
    
    # [TODO] allow the user to select one out of the top ten results

    result = results_list[0]

    LOGGER.log(logging.DEBUG, f"{result}")

    url = f"https://www.youtube.com/watch?v={result["id"]["videoId"]}"

    return await self.play_url(ctx, url)

  @commands.hybrid_command(brief="know what you'r listening to", description="get the current streamed resource information")
  async def playing(self, ctx : commands.Context):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    em = discord.Embed(title="", description=f"**Playing** **[{audio_stream.audio.title}]({audio_stream.audio.original_url})**", color=getDiscordMainColor())

    if (audio_stream.audio.is_live == True):
      em.description += " (live)"

    if (audio_stream.is_paused()):
      em.description += " (paused)"

    em.set_image(url=audio_stream.audio.thumbnail)

    await ctx.send(embed=em)
    return

  @commands.hybrid_command(brief="play/pause music", description="toggle audio stream. If on pause it resumes, and pauses otherwhise")
  async def pause(self, ctx : commands.Context):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    em = discord.Embed(description="", color=getDiscordMainColor())

    if audio_stream.is_paused():
      audio_stream.resume_stream()
      em.description += "resuming"
    else:
      audio_stream.pause_stream()
      em.description += "pausing"

    await ctx.send(embed=em)
    return

  async def __queue_show(self, ctx : commands.Context, length : int = 10):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    em = discord.Embed(title=f"{audio_stream.queue.count()} on queue", description="", color=getDiscordMainColor())

    if audio_stream.queue.count() == 0:
      em.description = "The queue is empty. Run `!play <link>` to play something"
      await ctx.send(embed=em)
      return

    for i in range(length):
      if audio_stream.queue.count() == i:
        break

      audio : AudioResource = audio_stream.queue.get(i)

      em.description += f"\n{i+1} - {audio.title}"

    await ctx.send(embed=em)

  @commands.hybrid_group(brief="know/edit the upcoming songs", description="get a list of the songs on queue. <length> specifies the max number to include, defaults to 10", invoke_without_command=False)
  async def queue(self, ctx : commands.Context, length : int = 10):
    return await self.__queue_show(ctx, length)

  @queue.command(name="show")
  async def queue_show(self, ctx : commands.Context, length : int = 10):
    return await self.__queue_show(ctx, length)

  @queue.command(name="shuffle", brief="", description="")
  async def queue_shuffle(self, ctx : commands.Context):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    audio_stream.queue.shuffle()

    em = discord.Embed(description="queue shuffled", color=getDiscordMainColor())
    await ctx.send(embed=em)

  @queue.command(name="flush", brief="clear the queue", description="delete all upcoming songs on queue")
  async def queue_flush(self, ctx : commands.Context):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    audio_stream.queue.clear()

    em = discord.Embed(color=getDiscordMainColor())
    em.description = "queue flushed"

    ctx.send(embed=em)

  @queue.command(name="pop", brief="delete a song from the queue", description="delete the given <index> from the queue, to know the index of a song use `/queue show`")
  async def queue_pop(self, ctx : commands.Context, index : int = 0):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    audio : AudioResource = audio_stream.queue.pop(index - 1)

    em = discord.Embed(color=getDiscordMainColor())

    em.description = f"{index} - {audio.title} removed"

    await ctx.send(embed=em)

  @commands.hybrid_command(brief="skip the current song", description="skip the current song")
  async def skip(self, ctx : commands.Context):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    em = discord.Embed(description="skiped", color=getDiscordMainColor())

    audio_stream.skip_stream()

    await ctx.send(embed=em)
    return
  
  @commands.hybrid_command(brief="stop playing", description="stop the audio stream and disconect from voice channel")
  async def stop(self, ctx : commands.Context):
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot)

    await audio_stream.stop_stream()

    em = discord.Embed(color=getDiscordMainColor())

    em.description = "stoping"

    await ctx.send(embed=em)

  @commands.hybrid_command(brief="speed up the current song", description="modify audio tempo by <speed> factor, accepts values in range [0.5, 5], doesn't work in livestreams")
  async def speed(self, ctx, speed : float):
    em = discord.Embed(color=getDiscordMainColor())
    
    if speed < 0 or speed > 5:
      em.description = "Invalid speed"
      return await ctx.send(embed=em)
    
    audio_stream = AudioStreamsHandler.get_stream(ctx.guild.id, self.bot) 

    if audio_stream.audio.is_live:
      em.description = "`!speed` doesn't work with livestreams"
      return await ctx.send(embed=em)

    em.description = f"Changing speed..."
    msg = await ctx.send(embed=em)

    audio_stream.set_speed(speed)

    em.description = f"Speed X{speed}"
    await msg.edit(embed=em)

  async def __playlist_show(self, ctx : commands.Context, index = -1):
    em = discord.Embed(description="", color=getDiscordMainColor())

    try:

      cursor =  DB_CONNECTION.cursor()

      if index == -1:
        sql = "SELECT name FROM playlists WHERE ownerUserId = ? ORDER BY rowId;"

        cursor.execute(sql, [ctx.author.id])

        rows = cursor.fetchall()

        em.title = f"{ctx.author.display_name} playlists"
        
        if len(rows) == 0:
          em.description = "no playlists yet, crete one with `!playlist create <name>`"
        
        else:
          for i, row in enumerate(rows):
            em.description += f"\n{i + 1} {row[0]}"
      
      else:
        playlist : AudioPlaylist = AudioPlaylist(index, ctx.author.id)

        em.title = f"{playlist.name} ({playlist.item_count} items)"

        if playlist.item_count == 0:
          em.description = "no items on the playlist, add one with `!playlist add <playlist_index> <url>`"
        
        else:
          for i, item in enumerate(playlist.items):
            em.description += f"{i + 1} {item.title}"

      await ctx.send(embed=em)

    except Exception as e:
      if DB_CONNECTION.in_transaction:
        DB_CONNECTION.rollback()
      
      LOGGER.log(logging.ERROR, f"Exception on playlist_show command:\n{repr(e)}")

    finally:
      cursor.close()

  @commands.hybrid_group()
  async def playlist(self, ctx, index : int = -1):
    return await self.__playlist_show(ctx, index)

  @playlist.command(name="show", brief="", description="")
  async def playlist_show(self, ctx : commands.Context, index : int = -1):
    return await self.__playlist_show(ctx, index)
  
  @playlist.command(name="create", brief="", description="")
  async def playlist_create(self, ctx : commands.Context, name : str):
    try:
      cursor =  DB_CONNECTION.cursor()

      sql = "INSERT INTO playlists(name, ownerUserId) VALUES (?, ?);"

      cursor.execute(sql, [name, ctx.author.id])

      DB_CONNECTION.commit()

      em = discord.Embed(color=getDiscordMainColor())

      em.description = f"playlist **\"{name}\"** created"

      await ctx.send(embed=em)

    except:
      if DB_CONNECTION.in_transaction:
        DB_CONNECTION.rollback()
      
      LOGGER.log(logging.ERROR, f"Exception on playlist_create command:\n{repr(e)}")

    finally:
      cursor.close()

  playlist.command()
  async def playlist_add(self, ctx : commands.Context, index : int, url : str):
    em = discord.Embed(color=getDiscordMainColor())

    try:
      cursor =  DB_CONNECTION.cursor()

      # get the playlist
      try:
        playlist = AudioPlaylist(index, ctx.author.id)
      except IndexError as e: 
        em.description = "Invalid index"
        return await ctx.send(embed=em)
      
      # check the url resource
      ytdlopts = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        "external_downloader_args": ['-loglevel', 'panic'],
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
      }

      ytdl = yt_dlp.YoutubeDL(ytdlopts)
      data = ytdl.extract_info(url=url, download=False)

      # add the item to playlist
      item : AudioPlaylistItem = playlist.new_item()

      item.load_data(data)

      playlist.add(item)

      em.description = f"[{item.title}]({item.original_url}) added to playlist {playlist[1]}"

      await ctx.send(embed=em)

    except:
      if DB_CONNECTION.in_transaction:
        DB_CONNECTION.rollback()
      
      LOGGER.log(logging.ERROR, f"Exception on playlist_create command:\n{repr(e)}")

    finally:
      cursor.close()

  playlist.command()
  async def playlist_remove(self, ctx : commands.Context, playlist_index : int, item_index : int):
    em = discord.Embed(color=getDiscordMainColor())

    try:
      playlist : AudioPlaylist = AudioPlaylist(playlist_index, ctx.author.id)
    except IndexError:
      em.description = "Invalid playlist index"
      return await ctx.send(embed=em)
    
    try:
      item : AudioPlaylistItem = playlist.remove(item_index)
    except IndexError:
      em.description = "Invalid item index"
      return await ctx.send(embed=em)
    
    em.description = f"{item.title} removed from {playlist.name} playlist"
    return await ctx.send(embed=em)

  async def __comment_get(self, ctx : commands.Context, youtube_url : str, category : str):
    em = discord.Embed(title="", description="", color=getDiscordMainColor())

    em.description = f"Quering [resource]({youtube_url})"

    msg : discord.Message = await ctx.send(embed=em)

    comments_list = process_youtube_comments(youtube_url, [category])

    if not comments_list.empty:
      comment = comments_list.comments
      
      for comment in comments_list.comments:
        print(comment)

        em.description += comment

    else:
      em.description = f"no youtube comment that is positive about <{category}>"

    await msg.edit(embed=em)

  @commands.hybrid_group()
  async def comment(self, ctx, youtube_url : str, category : str):
    return await self.__comment_get(ctx, youtube_url, category)
  
  @comment.command(name="get", brief="", description="")
  async def comment_get(self, ctx, youtube_url : str, category : str):
    return await self.__comment_get(ctx, youtube_url, category)