import discord
from discord.ext import tasks, commands
import yt_dlp

import os
import asyncio
import random

from variousUtils import getDiscordMainColor
import youtubeUtils
import guildStorage
from settings import *
from pydub import AudioSegment

class MusicPlayer(commands.Cog):
  """The music player command interface"""

  def __init__(self, bot : commands.Cog):
    self.bot = bot

  async def sound_stream(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)

    guild = self.bot.get_guild(ctx.guild.id)
    voice_client = guild.voice_client

    if voice_client:
      if len(voice_client.channel.members) == 1:
        print("exiting stream")
        storage.sound_stream.stop()
        storage.sound_stream = None

        # reset autoplay options
        storage.isAutoPlay = False
        storage.autoPlayInclusions = []
        storage.autoPlayExclusions = []

        await voice_client.disconnect()
        return

    if storage.isAutoPlay and not storage.queue:
      search = youtubeUtils.get_video_seach("music video", storage.autoPlayInclusions, storage.autoPlayExclusions, _type="video", _videoEmbeddable="true", _videoDuration="medium")

      for item in search:
        video_id = item["id"]["videoId"]
        video_title = item["snippet"]["title"]

        if not video_id in storage.autoPlayExclusions:
          storage.queue.append(video_id, video_title)
          break

    if storage.queue and voice_client:
      video_info = storage.queue.pop(0)
      video_id = video_info["video_id"]
      video_title = video_info["video_title"]

      # buscamos si existe en el buffer, si no, intentamos descargarlo
      if not os.path.exists(f"./buffer/{video_id}.mp3"):
        await self.__download(f"https://www.youtube.com/watch?v={video_id}", video_id)

      # reproducimos en discord
      if os.path.exists(f"./buffer/{video_id}.mp3"):
        storage.playing_video = video_info

        if storage.isAutoPlay:
          storage.autoPlayExclusions.append(video_id)

        voice_client.play(discord.FFmpegPCMAudio(f"./buffer/{video_id}.mp3"))

        while True: # espera a que termine la canción 
          await asyncio.sleep(2)
          if not voice_client.is_playing() and not voice_client.is_paused():
            break

      os.remove(f"./buffer/{video_id}.mp3")

    else:
      storage.sound_stream.stop()
      storage.sound_stream = None

      if voice_client: await voice_client.disconnect()

  @commands.group(brief="play some music", description="reproduce the given youtube video or playlist url audio on voice channel", invoke_without_command=True)
  async def play(self, ctx, url = commands.parameter(default="", description="a youtube video or playlist url")):
    LOGGER.log(logging.INFO, f"play called (Guild ID: {ctx.guild.id})")
    
    storage = guildStorage.get_storage(ctx.guild.id)
  
    if not ctx.author.voice:
      em = discord.Embed(title="Error", description="conéctate a un canal de voz", color=getDiscordMainColor())
      return await ctx.send(embed=em)
  
    # conectamos a un canal, si no estamos en uno ya
    voice_channel = ctx.guild.voice_client
    if not voice_channel:
      voice_channel = await ctx.author.voice.channel.connect()

    videos_info = youtubeUtils.get_videos_info_from_url(url)

    # agregamos la(s) canciones a la queue
    if(videos_info):
      for info in videos_info:
        storage.queue.append(info["video_id"], info["video_title"])
    else:
      em = discord.Embed(title="Error", description="not a valid url", color=getDiscordMainColor())
      return await ctx.send(embed=em)

    # elimina el mensaje para no causar spam
    await ctx.message.delete()

    # mostramos la(s) cancion(es) a agregar
    more_text = f" and {len(videos_info) - 1} more" if len(videos_info) > 1 else ""
    if len(storage.queue) == len(videos_info):
      em = discord.Embed(description=f"playing \"{videos_info[0]['video_title']}\"{more_text} ...", color=getDiscordMainColor())
    else:
      em = discord.Embed(description=f"appending \"{videos_info[0]['video_title']}\"{more_text} to queue...", color=getDiscordMainColor())

    await ctx.send(embed=em)

    await self.__safe_start_sound_stream(ctx)

  @play.command(name="search") 
  async def play_search(self, ctx, query = commands.parameter(default="", description="a youtube video title, if using spaces this should be contain within \"\"")):
    LOGGER.log(logging.INFO, f"play search called (Guild ID: {ctx.guild.id})")
    storage = guildStorage.get_storage(ctx.guild.id)
  
    if not ctx.author.voice:
      em = discord.Embed(title="Error", description="conéctate a un canal de voz", color=getDiscordMainColor())
      return await ctx.send(embed=em)
  
    # conectamos a un canal, si no estamos en uno ya
    voice_channel = ctx.guild.voice_client
    if not voice_channel:
      voice_channel = await ctx.author.voice.channel.connect()

    search = youtubeUtils.get_videos_search_from_query(query)[0]

    # agregamos la(s) canciones a la queue
    title = search["snippet"]["title"]
    id = search["id"]["videoId"]

    storage.queue.append(id, title)

    # elimina el mensaje para no causar spam
    await ctx.message.delete()

    # mostramos la(s) cancion(es) a agregar
    if not storage.queue:
      em = discord.Embed(description=f"playing best result: \"{title}\"", color=getDiscordMainColor())
      await ctx.send(embed=em)
    else:
      em = discord.Embed(description=f"appending best result: \"{title}\" to queue...", color=getDiscordMainColor())
      await ctx.send(embed=em)

    await self.__safe_start_sound_stream(ctx)

  @play.command(name="auto", description="Enhance the playlist by automatically queuing songs that match the given category, if non provided this will turn off autoplay mode.")
  async def play_auto(self, ctx, category = commands.parameter(default="", description="video categorie to look for, for example \"lofi\" will start auto addition of lofi style music.")):
    LOGGER.log(logging.INFO, f"play auto called (Guild ID: {ctx.guild.id})")

    storage = guildStorage.get_storage(ctx.guild.id)

    if category != "":
      if not ctx.author.voice:
        em = discord.Embed(title="Error", description="conéctate a un canal de voz", color=getDiscordMainColor())
        return await ctx.send(embed=em)
    
      # conectamos a un canal, si no estamos en uno ya
      voice_channel = ctx.guild.voice_client
      if not voice_channel:
        voice_channel = await ctx.author.voice.channel.connect()

      storage.isAutoPlay = True
      storage.autoPlayInclusions.append(category)
      title = "Autoplay mode is on"
      description = f"Now looking for songs matching \"{category}\""

      storage.autoPlayExclusions.append("cover")
      storage.autoPlayExclusions.append("shorts")
      storage.autoPlayExclusions.append("live")
      storage.autoPlayExclusions.append("livestream")

    else:
      storage.isAutoPlay = False
      storage.autoPlayInclusions = []
      storage.autoPlayExclusions = []

      title = "Autoplay mode is off"
      description = f""

    em = discord.Embed(title=title, description=description, color=getDiscordMainColor())
    await ctx.send(embed=em)

    await self.__safe_start_sound_stream(ctx)

  @play.command(name="default", description="Add all the songs from the default server playlist to queue", hidden=True)
  async def play_default(self, ctx):
    LOGGER.log(logging.INFO, f"play default called (Guild ID: {ctx.guild.id})")
    
    storage = guildStorage.get_storage(ctx.guild.id)

    #ensure author is connected to a voice channel
    if not ctx.author.voice:
      em = discord.Embed(title="Error", description="conéctate a un canal de voz", color=getDiscordMainColor())
      return await ctx.send(embed=em)
    
    #connect to a voice channel if not in one already
    voice_channel = ctx.guild.voice_client
    if not voice_channel:
      voice_channel = await ctx.author.voice.channel.connect()

    #get the playlist from long term storage
    videos_list = []
    with open("./default.txt", "r") as file:
      videos_list = file.readlines()

    #add songs to playlist
    for video in videos_list:
      title = video.split(",")[0]
      url = video.split(",")[1]

      storage.queue.append(youtubeUtils.get_video_id_from_video_url(url), title)

    if len(storage.queue) == len(videos_list):
      description = f"Now playing {storage.queue.get_video_title(0)}... from default playlist"
    else:
      description = f"appending {storage.queue.get_video_title(0)} and {len(videos_list) - 1} other to queue, from default playlist"

    em = discord.Embed(description=description, color=getDiscordMainColor())
    await ctx.send(embed=em)

    #start the stream
    await self.__safe_start_sound_stream(ctx)
    

  @commands.command(brief="pause playing", description="pause the current audio playing, to resume use !resume")
  async def pause(self, ctx):
    LOGGER.log(logging.INFO, f"pause called (Guild ID: {ctx.guild.id})")
    voice_channel = ctx.voice_client

    if voice_channel:
      if voice_channel.is_playing():
        em = discord.Embed(description="pausing...", color=getDiscordMainColor())
        await ctx.send(embed=em)
        voice_channel.pause()

  @commands.command(brief="change streaming speed", description="speed up or slow down by a factor between 0.5 and 4", hidden=True)
  async def speed(self, ctx, stretch_value=1.0):
    LOGGER.log(logging.INFO, f"speed called (Guild ID: {ctx.guild.id})")

    voice_channel = ctx.voice_client
    storage = guildStorage.get_storage(ctx.guild.id)

    if voice_channel:
      if voice_channel.is_playing():
        voice_channel.pause()
        if storage.playing_video["video_id"]:
          em = discord.Embed(description="changing speed...", color=getDiscordMainColor())
          await ctx.send(embed=em)
          playing_video_id = storage.playing_video["video_id"]
          audio = AudioSegment.from_mp3(f"./buffer/{playing_video_id}.mp3")
          edit_audio = audio.speedup(playback_speed=stretch_value) 
          edit_audio.export(f"./buffer/{playing_video_id}.mp3", format="mp3")
          voice_channel.resume()
        else:
          message = "use !play <url> to hear some music"
          em = discord.Embed(title="Error", description=message, color=getDiscordMainColor())
          await ctx.send(embed=em)

  @commands.command(brief="resume playing", description="resume the last audio playing")
  async def resume(self, ctx):
    LOGGER.log(logging.INFO, f"resume called (Guild ID: {ctx.guild.id})")
    voice_channel = ctx.voice_client
    
    if voice_channel:
      if voice_channel.is_paused():
        em = discord.Embed(description="resuming...", color=getDiscordMainColor())
        await ctx.send(embed=em)
        voice_channel.resume()

  @commands.command(brief="stops playing", description="stops audio reproduction and clears all currently queued sontgs")
  async def stop(self, ctx):
    LOGGER.log(logging.INFO, f"stop called (Guild ID: {ctx.guild.id})")
    storage = guildStorage.get_storage(ctx.guild.id)
    voice_channel = ctx.voice_client

    # flush the song queue
    storage.queue = guildStorage.SongQueue()

    # reset autoplay options
    storage.isAutoPlay = False
    storage.autoPlayInclusions = []
    storage.autoPlayExclusions = []

    await voice_channel.disconnect()
    await self.__safe_kill_sound_stream(ctx)

  @commands.command(brief="know what song you are hearing", description="retrives information about the current audio playing")
  async def playing(self, ctx):
    LOGGER.log(logging.INFO, f"playing called (Guild ID: {ctx.guild.id})")

    storage = guildStorage.get_storage(ctx.guild.id)
    
    message = ""

    message_id = ctx.message.id
    msg = await ctx.channel.fetch_message(message_id)

    if storage.playing_video["video_id"]:
      playing_video_id = storage.playing_video["video_id"]

      info = youtubeUtils.get_video_snippet_from_video_id(playing_video_id)

      # message = f"playing: {info["title"]}"
      em = discord.Embed(title=info["title"], color=getDiscordMainColor())
      thumb = 'https://img.youtube.com/vi/' + playing_video_id + '/mqdefault.jpg'
      em.set_image(url=thumb)
      await msg.reply(embed=em, mention_author=True)
    else:
      message = "use !play <url> to hear some music"
      em = discord.Embed(title="Error", description=message, color=getDiscordMainColor())
      await msg.reply(embed=em, mention_author=True)

    # elimina el mensaje para no causar spam
    await msg.delete()

  @commands.group(brief="show the queue", description="shows the current song queue", invoke_without_command=True)
  async def queue(self, ctx):
    LOGGER.log(logging.INFO, f"queue called (Guild ID: {ctx.guild.id})")

    storage = guildStorage.get_storage(ctx.guild.id)
    
    if storage.queue:
    #   snippet = youtubeUtils.get_video_snippet_from_video_id()

      title=f"{len(storage.queue)} songs on queue"
      description = f"up next: {storage.queue[0]['video_title']}"

      em = discord.Embed(title=title, description=description, color=getDiscordMainColor())

      await ctx.send(embed=em, mention_author=True)
    else:
      em = discord.Embed(description="Add stuff to the queue!", color=getDiscordMainColor())
      await ctx.send(embed=em, mention_author=True)

  @queue.command(name="list")
  async def queue_list(self, ctx, max_index = 10):
    LOGGER.log(logging.INFO, f"queue list called (Guild ID: {ctx.guild.id})")
    storage = guildStorage.get_storage(ctx.guild.id)

    if storage.queue:
      title=f"{len(storage.queue)} songs on queue"
      description = ""

      for i in range(len(storage.queue)):
        if(i > max_index): 
          break

        description += f"{i} - {storage.queue[i]['video_title']}\n"

      em = discord.Embed(title=title, description=description, color=getDiscordMainColor())

      await ctx.send(embed=em, mention_author=True)

  @commands.command(brief="clear the queue", description="clears all currently queued songs")
  async def flush(self, ctx):
    LOGGER.log(logging.INFO, f"flush called (Guild ID: {ctx.guild.id})")
    storage = guildStorage.get_storage(ctx.guild.id)
    # voice_channel = ctx.voice_client

    # flush the song queue
    storage.queue = guildStorage.SongQueue()

  @commands.command(brief="skip the current song", description="stops audio playing for the current song and plays another from the queue, by default the next one")
  async def skip(self, ctx, queue_index = commands.parameter(default=0, description="skip to this position in the queue")):
    LOGGER.log(logging.INFO, f"skip called (Guild ID: {ctx.guild.id})")
    storage = guildStorage.get_storage(ctx.guild.id)
    voice_channel = ctx.voice_client

    if len(storage.queue) >= queue_index:
      em = discord.Embed(description="skiping...", color=getDiscordMainColor())
      await ctx.send(embed=em)

      # pop every song that is before
      for _ in range(queue_index):
        storage.queue.pop(0)

      if voice_channel.is_playing():
        voice_channel.stop()

      if storage.sound_stream:
        await self.__safe_kill_sound_stream(ctx)

      await self.__safe_start_sound_stream(ctx)

  @commands.command(brief="mix it up", description="changes the orden in which the upcomig songs on queue will be played")
  async def shuffle(self, ctx):
    LOGGER.log(logging.INFO, f"shuffle called (Guild ID: {ctx.guild.id})")
    storage = guildStorage.get_storage(ctx.guild.id)

    if storage.queue:
      random.shuffle(storage.queue)

      video_id = storage.queue[0]["video_id"]
      info = youtubeUtils.get_video_snippet_from_video_id(video_id)

      em = discord.Embed(title="Queue shuffled", description=f"up next: {info['title']}", color=getDiscordMainColor())

      await ctx.send(embed=em)

  ########################   utils   ########################
      
  # this method will handle creating or obtaining a sound_stream task that is related with a sepcific guild (i.e. making a new thread for each guild)
  async def __get_sound_stream(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)

    if storage.sound_stream == None:
      storage.sound_stream = tasks.loop(seconds=5)(self.sound_stream)

    return storage.sound_stream

  async def __start_sound_stream(self, ctx):
    sound_stream = await self.__get_sound_stream(ctx)
    sound_stream.start(ctx)

  async def __safe_start_sound_stream(self, ctx):
    sound_stream = await self.__get_sound_stream(ctx)

    if not sound_stream.is_running():
      sound_stream.start(ctx)

  async def __safe_kill_sound_stream(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)
    sound_stream = storage.sound_stream

    if sound_stream:
      if sound_stream.is_running():
        sound_stream.cancel()

    storage.sound_stream = None

  async def __download(self, url, file_name = "song"):
    # buscamos el/los archivos en youtube
    options = {
      "postprocessors":[{
      "key": "FFmpegExtractAudio", # download audio only
      "preferredcodec": "mp3", # other acceptable types "wav" etc.
      "preferredquality": "192" # 192kbps audio
      }],
      "format": "bestaudio/best",
      "outtmpl": f"buffer/{file_name}", # downloaded file name
      "noplaylist": True, # Add the --no-playlist option
      "ignoreerrors" : True
    }

    with yt_dlp.YoutubeDL(options) as dl:
      dl.download([url]) #ver si aqui se puede evitar descargarlo y que se guarde en la ram