import discord
import sqlite3
from discord.ext import commands

import logging

from utils import permissionsUtils 

from settings import KUVA_GUILD_ID, DEV_GUILD_ID, DB_CONNECTION, DB_FILE_PATH, LOGGER

class KuvaCog(commands.Cog):
  """ Kuva Clan Commands """

  def __init__(self, bot : commands.Bot):
    self.bot = bot

    self.connection = DB_CONNECTION
    self.list_storage_file = "./kuva_movies.txt"

  async def cog_check(self, ctx):
    result = True
    
    result = result and ctx.guild.id in (KUVA_GUILD_ID, DEV_GUILD_ID) # this commands are only available for the kuva server
  
    result = result and permissionsUtils.cog_allowed_in_context(ctx, self)
  
    return result

  async def cog_before_invoke(self, ctx: commands.Context):
    LOGGER.log(logging.INFO, f"{ctx.command.name} called by {ctx.author.display_name} (USER ID: {ctx.author.id}) (GUILD ID: {ctx.guild.id})")
    self.cursor = self.connection.cursor()

  async def cog_after_invoke(self, ctx: commands.Context):
    self.cursor.close()

  @commands.group(name="movie")
  async def movie(self, ctx : commands.Context):

    try:
      sql = "INSERT INTO movie_list (title, imdb_url, score, author_user_id, guild_id) VALUES (?, ?, ?, ?, ?)"

      params = [
        "my favorite movie",
        "https://imdb_url.com.mx",
        5.68,
        ctx.author.id,
        ctx.guild.id
      ]

      self.cursor.execute(sql, params)
    
      self.connection.commit()

    except Exception as e:
      if self.connection.in_transaction:
        self.connection.rollback()
      
      LOGGER.log(logging.ERROR, f"Exception on movie_add command:\n{repr(e)}")

    finally:
      self.cursor.close()

  # @movie.command(name="add")
  # async def movie_add():
  #   pass

  # @discord.app_commands(name="addMovie")
  # async def add_movie(self, interaction : discord.Interaction):
  #   pass