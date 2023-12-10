import discord
from discord.ext import tasks, commands
import yt_dlp

import os
import asyncio
import random

import youtubeUtils

class MusicPlayer(commands.Cog):
  """The music player command interface"""

  def __init__(self, bot : commands.Cog):
    self.bot = bot

    self.playing_video_id = None
    self.voice_channel = None

    self.queue = []
    # NOTE the queue should store dictionaries with the following structure:
    # self.queue[n] = {
    #   video_id = ...
    #   video_title = ...
    # }

  # @commands.Cog.listener() # no me sale lo de los app commands
  # async def on_ready(self):
  #   print("MusicPlayer cog loaded")

  # @commands.command()
  # async def sync(self, ctx):
  #   fmt = await ctx.bot.tree.sync(guild=ctx.guild)
  #   await ctx.send(f"Synced {len(fmt)} commands")

  # @discord.app_commands.command()
  # async def test(self, interaction: discord.Interaction):
  #   await interaction.response.send_message(content="wololo")

  @tasks.loop(seconds=1)
  async def sound_stream(self):
    try:

      if self.queue and self.voice_channel:
        video_id = self.queue.pop(0)["video_id"]
        self.playing_video_id = video_id

        # buscamos si existe en el buffer, si no, intentamos descargarlo
        if not os.path.exists(f"./buffer/{video_id}.mp3"):
          await self.__download(f"https://www.youtube.com/watch?v={video_id}", video_id)

        # reproducimos en discord
        if os.path.exists(f"./buffer/{video_id}.mp3"):
          self.voice_channel.play(discord.FFmpegPCMAudio(f"./buffer/{video_id}.mp3"))

          while True: # espera a que termine la canción 
            await asyncio.sleep(2)
            if not self.voice_channel.is_playing() and not self.voice_channel.is_paused():
              break

          os.remove(f"./buffer/{video_id}.mp3")

      else:
        await self.__kill_sound_stream()

    except discord.ClientException: #se levanta en caso de que este desconectado el canal, fallas en el internet probablemente...
      print("voice client disconected!!!")
      # self.voice_channel.connect()
    except Exception as error:
      print(error) 

  @commands.group(brief="play some music", description="reproduce the given youtube video or playlist url audio on voice channel", invoke_without_command=True)
  async def play(self, ctx, url = commands.parameter(default="", description="a youtube video or playlist url")):
    if not ctx.author.voice:
        return await ctx.send("conectate a un canal de voz")
    
    # conectamos a un canal, si no estamos en uno ya
    voice_channel = ctx.guild.voice_client
    if not voice_channel:
      voice_channel = await ctx.author.voice.channel.connect()

    self.voice_channel = voice_channel
    
    # agregamos la(s) canciones a la queue
    videos_info = youtubeUtils.get_videos_info_from_url(url)
    if(videos_info):
      self.queue = self.queue + videos_info
    else:
      return await ctx.send("not a valid url") 
    
    # elimina el mensaje para no causar spam
    await ctx.message.delete()

    # inicia la reporduccion
    more_text = f" and {len(videos_info) - 1} more" if len(videos_info) > 1 else ""
    if not self.sound_stream.is_running():
      await ctx.send(f"playing \"{videos_info[0]["video_title"]}\"{more_text} ...")
      self.sound_stream.start()
    else:
      await ctx.send(f"appending \"{videos_info[0]["video_title"]}\"{more_text} to queue...")

  @play.command(name="search")
  async def play_search(self, ctx, query = commands.parameter(default="", description="a youtube video title, if using spaces this should be contain within \"\"")):
    if not ctx.author.voice:
        await ctx.send("conectate a un canal de voz")
        return
    
    # conectamos a un canal, si no estamos en uno ya
    voice_channel = ctx.guild.voice_client
    if not voice_channel:
      voice_channel = await ctx.author.voice.channel.connect()

    self.voice_channel = voice_channel

    search = youtubeUtils.get_videos_search_from_query(query)[0]

    title = search["snippet"]["title"]
    id = search["id"]["videoId"]

    self.queue.append({
      "video_id" : id,
      "video_title" : title
    })

    # elimina el mensaje para no causar spam
    await ctx.message.delete()

    # inicia la reporduccion
    if not self.sound_stream.is_running():
      await ctx.send(f"playing best result: \"{title}\"")
      await self.sound_stream.start()
    else:
      await ctx.send(f"appending best result: \"{title}\" to queue...")

  @commands.command(brief="stop playing", description="stops audio and clears all currently queued songs")
  async def cancel(self, ctx):
    if self.voice_channel:
      await self.__kill_sound_stream()

  @commands.command(brief="skip the current song", description="stops audio playing for the current song and plays another from the queue, by default the next one")
  async def skip(self, ctx, queue_index = commands.parameter(default=0, description="skip to this position in the queue")):
    if len(self.queue) - 1 >= queue_index:
      await self.voice_channel.stop()

      await ctx.send("skiping...")

      if os.path.exists(f"./buffer/{self.playing_video_id}.mp3"):
        os.remove(f"./buffer/{self.playing_video_id}.mp3")
      
      # pop every song that is before
      for _ in range(queue_index):
        self.queue.pop(0)

      if self.sound_stream.is_running():
        self.sound_stream.restart()

  @commands.command(brief="pause playing", description="pause the current audio playing, to resume use !resume")
  async def pause(self, ctx):
    if self.voice_channel:
      if self.voice_channel.is_playing():
        await ctx.send("pausing...")
        self.voice_channel.pause()

  @commands.command(brief="resume playing", description="resume the last audio playing")
  async def resume(self, ctx):
    if self.voice_channel:
      if self.voice_channel.is_paused():
        await ctx.send("resuming...")
        self.voice_channel.resume()

  @commands.command(brief="know what song you are hearing", description="retrives information about the current audio playing")
  async def playing(self, ctx):
    message = ""

    message_id = ctx.message.id
    msg = await ctx.channel.fetch_message(message_id)

    if self.playing_video_id:
      playing_video_id = self.playing_video_id

      info = youtubeUtils.get_video_snippet_from_video_id(playing_video_id)

      # message = f"playing: {info["title"]}"
      em = discord.Embed(title=info["title"], color=discord.Colour.red())
      thumb = 'https://img.youtube.com/vi/' + playing_video_id + '/mqdefault.jpg'
      em.set_image(url=thumb)
      await msg.reply(embed=em, mention_author=True)
    else:
      message = "use !play <url> to hear some music"
      await msg.reply(message, mention_author=True)

    # elimina el mensaje para no causar spam
    await msg.delete()

  @commands.group(brief="show the queue", description="shows the current song queue", invoke_without_command=True)
  async def queue(self, ctx):
    if self.queue:
      snippet = youtubeUtils.get_video_snippet_from_video_id(self.playing_video_id)

      title=f"{len(self.queue)} songs on queue"
      description = f"up next: {snippet['title']}"

      em = discord.Embed(title=title, description=description)

      await ctx.send(embed=em, mention_author=True)

  @queue.command(name="list")
  async def queue_list(self, ctx, max_index = 10):
    if self.queue:
      title=f"{len(self.queue)} songs on queue"
      description = ""

      for i in range(len(self.queue)):
        if(i > max_index): 
          break

        description += f"{i} - {self.queue[i]["video_title"]}\n"

      em = discord.Embed(title=title, description=description)

      await ctx.send(embed=em, mention_author=True)

  @commands.command(brief="mix it up", description="changes the orden in which the upcomig songs on queue will be played")
  async def shuffle(self, ctx):
    if self.queue:
      random.shuffle(self.queue)

      video_id = self.queue[0]["video_id"]
      info = youtubeUtils.get_video_snippet_from_video_id(video_id)

      em = discord.Embed(title="queue shuffled", description=f"up next: {info["title"]}")

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


# async def setup(bot: commands.Bot):
#   await bot.add_cog(MusicPlayer(bot))