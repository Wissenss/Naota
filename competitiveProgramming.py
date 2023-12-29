import discord
from discord.ext import tasks, commands

import CodeforcesAPI

import os
import asyncio
import random

from settings import *

# initialize youtube http api client
codeforces = CodeforcesAPI.Codeforces(api_key=CODEFORCES_TOKEN)

class CompetitiveProgramming(commands.Cog):
  """The competitive programming command interface"""

  @commands.command
  async def problem(brief="break out the algorithms", description="get a codeforces problem"):
    codeforces.contest()