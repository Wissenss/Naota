import discord
from discord.ext import tasks, commands

import CodeforcesAPI

import os
import asyncio
import random

from dotenv import load_dotenv

load_dotenv(override=True)

# initialize youtube http api client
CODEFORCES_TOKEN = os.getenv("CODEFORCES_TOKEN")

codeforces = CodeforcesAPI.Codeforces(api_key=CODEFORCES_TOKEN)

class CompetitiveProgramming(commands.Cog):
  """The competitive programming command interface"""

  @commands.command
  async def problem(brief="break out the algorithms", description="get a codeforces problem"):
    codeforces.contest()