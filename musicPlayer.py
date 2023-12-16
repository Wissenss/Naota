import discord
from discord.ext import tasks, commands
import yt_dlp

import os
import asyncio
import random

import youtubeUtils
import guildStorage

class MusicPlayer(commands.Cog):
  """The music player command interface"""

  def __init__(self, bot : commands.Cog):
    self.bot = bot

    self.sound_stream.start()

  @tasks.loop(seconds=1)
  async def sound_stream(self):
    for guild_id in guildStorage.get_storage_keys():
      storage = guildStorage.get_storage(guild_id)
      guild = self.bot.get_guild(guild_id)

      voice_client = guild.voice_client

      if not voice_client: continue

      #si no se esta tocando nada, intentamos borrar el ultimo reproducido
      if storage.playing_video and not voice_client.is_playing() and not voice_client.is_paused():
        video_id = storage.playing_video["video_id"]

        try:
          if os.path.exists(f"./buffer/{video_id}.mp3"):
            os.remove(f"./buffer/{video_id}.mp3")
        except:
          pass

      # si hay algo en la queue y no se esta tocando nada, iniciamos reproduccion
      if storage.queue and not voice_client.is_playing() and not voice_client.is_paused():
        video_info = storage.queue.pop(0)
        video_id = video_info["video_id"]
        video_title = video_info["video_title"]

        # buscamos si existe en el buffer, si no, intentamos descargarlo
        if not os.path.exists(f"./buffer/{video_id}.mp3"):
          await self.__download(f"https://www.youtube.com/watch?v={video_id}", video_id)

        if os.path.exists(f"./buffer/{video_id}.mp3"):
          storage.playing_video = video_info

          voice_client.play(discord.FFmpegPCMAudio(f"./buffer/{video_id}.mp3"))

      # si no hay nada en la queue, desconectamos del canal
      if not storage.queue and voice_client.is_connected() and not voice_client.is_playing() and not voice_client.is_paused():
        storage.playing_video = None
        storage.queue = guildStorage.SongQueue()
        await voice_client.disconnect()
        continue

  @commands.group(brief="play some music", description="reproduce the given youtube video or playlist url audio on voice channel", invoke_without_command=True)
  async def play(self, ctx, url = commands.parameter(default="", description="a youtube video or playlist url")):
    storage = guildStorage.get_storage(ctx.guild.id)
  
    if not ctx.author.voice:
      em = discord.Embed(title="Error", description="conéctate a un canal de voz", color=discord.Colour.random())
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
      em = discord.Embed(title="Error", description="not a valid url", color=discord.Colour.random())
      return await ctx.send(embed=em)

    # elimina el mensaje para no causar spam
    await ctx.message.delete()

    # mostramos la(s) cancion(es) a agregar
    more_text = f" and {len(videos_info) - 1} more" if len(videos_info) > 1 else ""
    if len(storage.queue) == len(videos_info):
      em = discord.Embed(description=f"playing \"{videos_info[0]["video_title"]}\"{more_text} ...", color=discord.Colour.random())
      await ctx.send(embed=em)
    else:
      em = discord.Embed(description=f"appending \"{videos_info[0]["video_title"]}\"{more_text} to queue...", color=discord.Colour.random())
      await ctx.send(embed=em)

  @play.command(name="search") #pending
  async def play_search(self, ctx, query = commands.parameter(default="", description="a youtube video title, if using spaces this should be contain within \"\"")):
    storage = guildStorage.get_storage(ctx.guild.id)
  
    if not ctx.author.voice:
      em = discord.Embed(title="Error", description="conéctate a un canal de voz", color=discord.Colour.random())
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
      em = discord.Embed(description=f"playing best result: \"{title}\"", color=discord.Colour.random())
      await ctx.send(embed=em)
    else:
      em = discord.Embed(description=f"appending best result: \"{title}\" to queue...", color=discord.Colour.random())
      await ctx.send(embed=em)

  @commands.command(brief="pause playing", description="pause the current audio playing, to resume use !resume")
  async def pause(self, ctx):
    voice_channel = ctx.voice_client

    if voice_channel:
      if voice_channel.is_playing():
        em = discord.Embed(description="pausing...", color=discord.Colour.random())
        await ctx.send(embed=em)
        voice_channel.pause()

  @commands.command(brief="resume playing", description="resume the last audio playing")
  async def resume(self, ctx):
    voice_channel = ctx.voice_client
    
    if voice_channel:
      if voice_channel.is_paused():
        em = discord.Embed(description="resuming...", color=discord.Colour.random())
        await ctx.send(embed=em)
        voice_channel.resume()

  @commands.command(brief="stops playing", description="stops audio reproduction and clears all currently queued sontgs")
  async def stop(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)
    voice_channel = ctx.voice_client

    # flush the song queue
    storage.queue = guildStorage.SongQueue()

    await voice_channel.disconnect()

  @commands.command(brief="know what song you are hearing", description="retrives information about the current audio playing")
  async def playing(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)
    
    message = ""

    message_id = ctx.message.id
    msg = await ctx.channel.fetch_message(message_id)

    if storage.playing_video["video_id"]:
      playing_video_id = storage.playing_video["video_id"]

      info = youtubeUtils.get_video_snippet_from_video_id(playing_video_id)

      # message = f"playing: {info["title"]}"
      em = discord.Embed(title=info["title"], color=discord.Colour.random())
      thumb = 'https://img.youtube.com/vi/' + playing_video_id + '/mqdefault.jpg'
      em.set_image(url=thumb)
      await msg.reply(embed=em, mention_author=True)
    else:
      message = "use !play <url> to hear some music"
      em = discord.Embed(title="Error", description=message, color=discord.Colour.random())
      await msg.reply(embed=em, mention_author=True)

    # elimina el mensaje para no causar spam
    await msg.delete()

  @commands.group(brief="show the queue", description="shows the current song queue", invoke_without_command=True)
  async def queue(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)
    
    if storage.queue:
    #   snippet = youtubeUtils.get_video_snippet_from_video_id()

      title=f"{len(storage.queue)} songs on queue"
      description = f"up next: {storage.queue[0]["video_title"]}"

      em = discord.Embed(title=title, description=description, color=discord.Colour.random())

      await ctx.send(embed=em, mention_author=True)

  @queue.command(name="list")
  async def queue_list(self, ctx, max_index = 10):
    storage = guildStorage.get_storage(ctx.guild.id)

    if storage.queue:
      title=f"{len(storage.queue)} songs on queue"
      description = ""

      for i in range(len(storage.queue)):
        if(i > max_index): 
          break

        description += f"{i} - {storage.queue[i]["video_title"]}\n"

      em = discord.Embed(title=title, description=description, color=discord.Colour.random())

      await ctx.send(embed=em, mention_author=True)

  @commands.command(brief="clear the queue", description="clears all currently queued songs")
  async def flush(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)
    # voice_channel = ctx.voice_client

    # flush the song queue
    storage.queue = guildStorage.SongQueue()

  @commands.command(brief="skip the current song", description="stops audio playing for the current song and plays another from the queue, by default the next one")
  async def skip(self, ctx, queue_index = commands.parameter(default=0, description="skip to this position in the queue")):
    storage = guildStorage.get_storage(ctx.guild.id)
    voice_channel = ctx.voice_client

    if len(storage.queue) - 1 >= queue_index:
      # pop every song that is before
      for _ in range(queue_index):
        storage.queue.pop(0)

      if voice_channel.is_playing():
        voice_channel.stop()

      em = discord.Embed(description="skiping...", color=discord.Colour.random())
      await ctx.send(embed=em)

      if os.path.exists(f"./buffer/{storage.playing_video["video_id"]}.mp3"):
        os.remove(f"./buffer/{storage.playing_video["video_id"]}.mp3")

  @commands.command(brief="mix it up", description="changes the orden in which the upcomig songs on queue will be played")
  async def shuffle(self, ctx):
    storage = guildStorage.get_storage(ctx.guild.id)

    if storage.queue:
      random.shuffle(storage.queue)

      video_id = storage.queue[0]["video_id"]
      info = youtubeUtils.get_video_snippet_from_video_id(video_id)

      em = discord.Embed(title="queue shuffled", description=f"up next: {info["title"]}", color=discord.Colour.random())

      await ctx.send(embed=em)

  ########################   utils   ########################
  async def __kill_sound_stream(self):
    await self.voice_channel.disconnect()
    self.voice_channel.cleanup()
    self.voice_channel = None
    self.queue = []
    self.playing_video_id = None
    self.sound_stream.cancel()

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