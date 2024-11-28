import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
import git
import time
import datetime
import os
from utils import permissionsUtils, achivementsUtils

from cogs.customCog import CustomCog

import subprocess

# Example usage
# if __name__ == "__main__":
#     run_program_in_user_session("C:\\Path\\To\\YourProgram.exe")

class KeyboardCog(CustomCog):
  def __init__(self, bot : commands.Bot):
    super().__init__(bot)

    self.__cog_name__ = "Keyboard"

  @commands.hybrid_command(brief="press space", description="press the spacebar")
  async def space(self, ctx : commands.Context):
    subprocess.run("python C:\\Users\\Leo\\Dev\\Naota\\cli.py space")