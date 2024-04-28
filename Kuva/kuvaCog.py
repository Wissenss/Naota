import discord
from discord.ext import commands

from settings import KUVA_GUILD_ID

class KuvaCog(commands.Cog):
  """ Kuva Clan Commands """

  def __init__(self, bot : commands.Bot):
    self.bot = bot

    self.list_storage_file = "./kuva_movies.txt"

  # @discord.app_commands(name="addMovie")
  # async def add_movie(self, interaction : discord.Interaction):
  #   pass