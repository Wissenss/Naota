import discord
from discord.ext import commands
import yt_dlp

import os
import asyncio

import youtubeService

class MusicPlayer(commands.Cog):
  """The music player command interface"""

  def __init__(self):
    self.queue = []
    self.play = False

  @commands.command(brief="play some music", description="reproduce the given youtube video or playlist url audio on voice channel (development)")
  async def play(self, ctx, url):
    if not ctx.author.voice.channel:
      await ctx.send("conectate a un canal de voz")
      return

    # conectamos a un canal, si no estamos en uno ya
    voice_channel = ctx.guild.voice_client
    if not ctx.guild.voice_client:
      voice_channel = await ctx.author.voice.channel.connect()

    # agregamos la(s) canciones a la queue
    self.queue = self.queue + youtubeService.get_videos_ids_from_url(url)

    # elimina el mensaje para no causar spam
    message_id = ctx.message.id
    msg = await ctx.channel.fetch_message(message_id)
    await msg.delete()

    # reproducimos cada cancion en la queue
    self.play = True
    while len(self.queue) and self.play:
      video_id = self.queue[0]

      #buscamos si existe en el buffer
      if not os.path.exists(f"./buffer/{video_id}.mp3"):
        await download(f"https://www.youtube.com/watch?v={video_id}", video_id)

      if os.path.exists(f"./buffer/{video_id}.mp3"):
        # reproducimos en discord
        voice_channel.play(discord.FFmpegPCMAudio(f"./buffer/{video_id}.mp3"))

        playing = voice_channel.is_playing()
        while playing and self.play: # espera a que termine la canción
          await asyncio.sleep(5)
          playing = voice_channel.is_playing()

        os.remove(f"./buffer/{video_id}.mp3")
      
      try:
        self.queue.pop(0)
      except:
        pass
    
    await voice_channel.disconnect()

  @commands.command(brief="stop playing", description="stops audio and clears all currently queued songs")
  async def cancel(self, ctx):
    print("cancel called")
    if ctx.guild.voice_client:
      self.play = False
      self.queue = []
      await ctx.guild.voice_client.disconnect()

  @commands.command(brief="know what song you are hearing", description="retrives information about the current audio playing")
  async def playing(self, ctx):
    message = ""
    
    if len(self.queue):
      playing_video_id = self.queue[0]

      info = youtubeService.get_video_info_from_id(playing_video_id)

      message = f"playing: {info["title"]}"
    else:
      message = "use !play <url> to hear some music"

    # elimina el mensaje para no causar spam
    message_id = ctx.message.id
    msg = await ctx.channel.fetch_message(message_id)
    await msg.reply(message, mention_author=True)
    await msg.delete()

  @commands.command(brief="show the queue list (development)", description="shows the current song queue (broken)")
  async def queue(self, ctx):
    await ctx.send(self.queue)

async def download(url, file_name = "song"):
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
