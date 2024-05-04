import os
import logging
import time
import datetime
import asyncio
import uuid
import random

import discord
from discord.ext import tasks, commands

from settings import LOGGER, LOG_LEVEL, YOUTUBE_TOKEN

import yt_dlp
from googleapiclient.discovery import build

from variousUtils import getDiscordMainColor


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
  __buffer_path = "./buffer"

  @staticmethod
  def __exists(filename : str):
    filepath = os.path.join(AudioBuffer.__buffer_path, filename)
    return os.path.isfile(filepath)

  @staticmethod
  def exists(resource : AudioResource):
    return AudioBuffer.__exists(f"{str(resource.uuid)}.mp3")

  @staticmethod
  def remove(resource : AudioResource):
    AudioBuffer.__remove(f"{str(resource.uuid)}.mp3")

  @staticmethod
  def __remove(filename : str):
    filepath = os.path.join(AudioBuffer.__buffer_path, filename)
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

  def start_stream(self, voice_channel : discord.VoiceClient):
    if self._stream_task.is_running():
      raise Exception("Stream is already running!")

    self.voice_channel = voice_channel

    self._stream_task.start()

  def stop_stream(self):
    if not self._stream_task.is_running():
      raise Exception("Stream is not running!")
    
    self.audio = None
    self.queue.clear()

    self._stream_task.cancel()

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

  async def __stream_task(self): # this is a loop, think of it as such: once the start_stream function is called this will run every second
    if self.voice_channel == None:
      return

    # disconnect and stop if no member on channel. it has a 5 second tolerance
    # print(f"members on channel: {len(self.voice_channel.channel.members)}") # for debug
    if len(self.voice_channel.channel.members) <= 1:
      await asyncio.sleep(5)
      if len(self.voice_channel.channel.members) <= 1:
        LOGGER.log(logging.INFO, f"stoping stream: no member on voice channel")
        await self.voice_channel.disconnect()
        self.stop_stream()
        return
    
    if self.voice_channel.is_paused():
      return

    if self.voice_channel.is_playing():
      return

    # if not playing and audio is not none, this means the song just ended, so we can delete the .mp3 file if any
    elif self.audio != None:
      if AudioBuffer.exists(self.audio):
        AudioBuffer.remove(self.audio)

    if self.queue.count() == 0:
      LOGGER.log(logging.INFO, f"stoping stream: no songs on queue")
      await self.voice_channel.disconnect()
      self.stop_stream()
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

    self.buffer_directory = "./buffer/"

    self.constant_buffer_purge.start()

  @tasks.loop(minutes=60)
  async def constant_buffer_purge(self):
    AudioBuffer.purge()

  async def cog_before_invoke(self, ctx : commands.Context):
    LOGGER.log(logging.INFO, f"{ctx.command.name} called (USER ID: {ctx.author.id}) (GUILD ID: {ctx.guild.id})")

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

    em.description = f"**Appending** **[{audio.title}]({url})**"

    if not audio_stream.is_running():
      audio_stream.start_stream(voice_channel)
      em.description = f"**Playing** **[{audio.title}]({url})**"

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

    em = discord.Embed(title="", description=f"**Playing** **[{audio_stream.audio.title}]({audio_stream.audio.url})**", color=getDiscordMainColor())

    if (audio_stream.is_paused()):
      em.description += " (paused) "

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

    audio_stream.stop_stream()

    em = discord.Embed(color=getDiscordMainColor())

    em.description = "stoping"

    await ctx.send(embed=em)