import io
import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
import git
import time
import datetime
import os
from utils import permissionsUtils, achivementsUtils
import connectionPool

from cogs.customCog import CustomCog

from cogs.musicPlayerCog import AudioBuffer

class AchivementCog (CustomCog):
    def __init__(self, bot : commands.Bot):
        super().__init__(bot)

        self.__cog_name__ = "Achivement"

    @commands.hybrid_command(brief="progress", description="test for correct bot connection")
    async def progress(self, ctx : commands.Context):
      # get the connection
      conn = connectionPool.get_connection()
      curs = conn.cursor()

      # get the total count of achivements
      curs.execute("SELECT COUNT(*) FROM achivements;")

      no_achivements = curs.fetchone()[0]

      LOGGER.log(logging.DEBUG, f"the total number of achivements is {no_achivements}")

      # obtain the completed achivements
      sql = "SELECT * FROM achivements_users WHERE user_id = (SELECT user_id FROM users WHERE discord_user_id = ?);"

      curs.execute(sql, [ctx.author.id])

      completed_achivements = 0

      for row in curs.fetchall():
        completed_achivements += row[3]

      LOGGER.log(logging.DEBUG, f"the number of completed achivements is {completed_achivements}")

      # release the connection
      connectionPool.release_connection(conn)

      # calculate how much progress a user have 
      progress = completed_achivements / no_achivements

      # create the progress bar
      image_progress = io.BytesIO()

      progress_bar_raw = achivementsUtils.create_progress_bar(progress)
      progress_bar_raw.save(image_progress, 'PNG')
      image_progress.seek(0)

      file = discord.File(image_progress, filename="progress.png")

      # send the embed
      em = discord.Embed(color=getDiscordMainColor())

      em.set_author(name=f"{ctx.author.display_name} progress", icon_url=ctx.author.display_avatar)

      em.set_image(url="attachment://progress.png")

      await ctx.send(file=file, embed=em)

    @commands.hybrid_command(brief="know the achivements", description="show a list of all obtainable achivements")
    async def achivements(self, ctx : commands.Context):
      # get the connection
      conn = connectionPool.get_connection()
      curs = conn.cursor()
      
      # get the list of achivements
      curs.execute("SELECT * FROM achivements a LEFT JOIN achivements_users au ON a.achivement_id = au.achivement_id AND user_id = (SELECT user_id FROM users WHERE discord_user_id = ?);", [ctx.author.id])
      rows = curs.fetchall()

      LOGGER.log(logging.DEBUG, f"the list of achivements is: \n{rows}")

      # close the connection
      connectionPool.release_connection(conn)

      # create the embed list
      em = discord.Embed(color=getDiscordMainColor())

      em.title = "Achivements"
      em.description = ""

      for row in rows:
        a_id = row[0]
        a_name = row[1]
        a_description = row[2]
        au_id = row[3]

        completed = au_id != None

        em.description += "\n~~" if completed else "\n"

        em.description += f"{a_id} - {a_name}"

        em.description += "~~" if completed else ""
          
      # send the list
      await ctx.send(embed=em)

      # grant the achivement
      await achivementsUtils.observe_achivement(1, ctx)

    @commands.hybrid_command(brief="how to get an achivement", description="show the description for a given achivement")
    async def achivementinfo(self, ctx : commands.Context, achivement_id : int):
      # get the connection
      conn = connectionPool.get_connection()
      curs = conn.cursor()

      # get the achivement record
      sql = "SELECT * FROM achivements a LEFT JOIN achivements_users au ON a.achivement_id = au.achivement_id AND user_id = (SELECT user_id FROM users WHERE discord_user_id = ?) WHERE a.achivement_id = ?;"

      curs.execute(sql, [ctx.author.id, achivement_id])

      row = curs.fetchone()

      LOGGER.log(logging.DEBUG, f"the achivement record is: {row}")

      # release the connection
      connectionPool.release_connection(conn)

      # send the information
      em = discord.Embed(description="", color=getDiscordMainColor())

      if row == None: # if the given achivement id does not exists we informa about it
        em.description = f"{achivement_id} is not a valida achivement id"
        em.color = discord.Color.red()
        return await ctx.send(embed=em)
      
      a_id = row[0]
      a_name = row[1]
      a_description = row[2]
      au_id = row[3]

      completed = au_id != None

      em.title = f"#{a_id}: {a_name}"

      em.description += f"\n**Description:** {a_description}"
      em.description += f"\n**Status:** {':trophy: completed!' if completed else 'pending'}"

      await ctx.send(embed=em)