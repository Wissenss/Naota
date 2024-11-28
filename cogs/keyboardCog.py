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

from multiprocessing.connection import Client

import connectionPool

import keyboard

class KeyboardCog(CustomCog):
  def __init__(self, bot : commands.Bot):
    super().__init__(bot)

    self.__cog_name__ = "Keyboard"

  @commands.hybrid_command(brief="press the spacebar", description="press the spacebar. All achivements must be completed for this action.")
  async def space(self, ctx : commands.Context):
    # get the connection
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    # get the list of achivements
    curs.execute("SELECT * FROM achivements a LEFT JOIN achivements_users au ON a.achivement_id = au.achivement_id AND user_id = (SELECT user_id FROM users WHERE discord_user_id = ?);", [ctx.author.id])
    rows = curs.fetchall()

    # close the connection
    connectionPool.release_connection(conn)

    # check if the user has completed all achivements
    for row in rows:
      a_id = row[0]
      a_name = row[1]
      a_description = row[2]
      au_id = row[3]

      completed = au_id != None

      if completed == False:
        em = discord.Embed(description="Complete all achivements to gain access to the keyboar commands. Types `!achivements` for more.", color=discord.Color.red())
        return await ctx.send(embed=em)

    # press the space bar
    em = discord.Embed(description="pressing space...", color=getDiscordMainColor())

    await ctx.send(embed=em)

    keyboard.press_and_release("space")