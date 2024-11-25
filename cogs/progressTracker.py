import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
import git
import time
import os
from utils import permissionsUtils

from cogs.customCog import CustomCog

class TrackerLog():
   def __init__(self):
      self.tracker_item_id = None
      self.tracker_id = None
      self.log = None
      self.date = None

class Tracker():
   def __init__(self):
      self.tracker_id = None
      self.tracker_type = None
      self.owner_id = None
      self.name = None
      self.status = None
      self.date = None
      self.logs = None

class ProgressTrackerCog (CustomCog):
    def __init__(self, bot : commands.Bot):
        super().__init__(bot)

        self.__cog_name__ = "ProgressTracker"

    def get_default_tracker_id(self) -> int:
      pass

    def create_tracker(self, owner_id : int, name : str, type : int = 0) -> int:
      pass

    def get_tracker(self) -> Tracker:
       pass

    @commands.hybrid_command(name="createTracker")
    async def create_tracker(self, ctx : commands.Context, name : str):
      self.create_tracker(name)

      tracker : Tracker = self.get_tracker()

      em = discord.Embed(title=f"Tracker #{tracker.tracker_id} created", description="", color=getDiscordMainColor())

      em.description += f"\nname: {tracker.name}"
      em.description += f"\ndate: {tracker.date}"

      await ctx.send(embed=em)

    @commands.hybrid_command(name="showTracker")
    async def show_tracker(self, ctx : commands.Context, tracker_id : int = 0):
      tracker = self.get_tracker()

      if tracker == None:
        return
       
      em = discord.Embed(title=f"Tracker #{tracker.tracker_id}: {tracker.name}", description="", color=getDiscordMainColor())

      
      


      
