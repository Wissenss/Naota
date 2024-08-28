import discord

from discord.ext import commands

import logging

from settings import CHEMS_GUILD_ID, DEV_GUILD_ID, DB_FILE_PATH, LOGGER
from utils.variousUtils import getDiscordMainColor
from utils import permissionsUtils

class ChemsCog(commands.Cog):
  """ Butthole Lovers Commands """

  def __init__(self, bot : commands.Bot):
    self.bot = bot
    self.storage_file = "cords.txt"

  async def cog_before_invoke(self, ctx: commands.Context):
    LOGGER.log(logging.INFO, f"{ctx.command.name} called by {ctx.author.display_name} (USER ID: {ctx.author.id}) (GUILD ID: {ctx.guild.id})")

  async def cog_check(self, ctx):
    result = True
    
    result = result and ctx.guild.id in (CHEMS_GUILD_ID, DEV_GUILD_ID) # this commands are only available for the butthole lovers server
  
    result = result and permissionsUtils.cog_allowed_in_context(ctx, self)
  
    return result

  async def __cords_show(self, ctx : commands.Context):
    em = discord.Embed(title="The Cords", description="", color=getDiscordMainColor())
    
    with open(self.storage_file) as file:
      for line in file.readlines():
        data = line.split(',')

        em.description += f"\n{data[0]}: {data[1]} / {data[2]} / {data[3]}"

    await ctx.send(embed=em)

  @commands.hybrid_group(brief="crud minecraft cords", description="CRUD for minecraft coordinates")
  async def cords(self, ctx : commands.context):
    await self.__cords_show(ctx)

  @cords.command(name="show", brief="show the cords")
  async def cords_show(self, ctx : commands.Context):
    await self.__cords_show(ctx)

  @cords.command(name="add", brief="add a cord")
  async def cords_add(self, ctx : commands.Context, name : str, x : int, y : int, z : int):
    with open(self.storage_file, 'a') as file:
      file.write(f"\n{name},{x},{y},{z}")

    await self.__cords_show(ctx)