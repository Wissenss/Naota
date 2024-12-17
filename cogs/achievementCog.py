import io
import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
import git
import time
import datetime
import os
from utils import permissionsUtils, achievementsUtils
import connectionPool

from cogs.customCog import CustomCog

from cogs.musicPlayerCog import AudioBuffer

class AchievementCog (CustomCog):
    def __init__(self, bot : commands.Bot):
        super().__init__(bot)

        self.__cog_name__ = "Achievement"

    @commands.hybrid_command(brief="progress", description="test for correct bot connection")
    async def progress(self, ctx : commands.Context):
      # get the connection
      conn = connectionPool.get_connection()
      curs = conn.cursor()

      # get the total count of achievements
      curs.execute("SELECT COUNT(*) FROM achivements;")

      no_achievements = curs.fetchone()[0]

      LOGGER.log(logging.DEBUG, f"the total number of achievements is {no_achievements}")

      # obtain the completed achievements
      sql = "SELECT * FROM achivements_users WHERE user_id = (SELECT user_id FROM users WHERE discord_user_id = ?);"

      curs.execute(sql, [ctx.author.id])

      completed_achievements = 0

      for row in curs.fetchall():
        completed_achievements += row[3]

      LOGGER.log(logging.DEBUG, f"the number of completed achievements is {completed_achievements}")

      # release the connection
      connectionPool.release_connection(conn)

      # calculate how much progress a user have 
      progress = completed_achievements / no_achievements

      # create the progress bar
      image_progress = io.BytesIO()

      progress_bar_raw = achievementsUtils.create_progress_bar(progress)
      progress_bar_raw.save(image_progress, 'PNG')
      image_progress.seek(0)

      file = discord.File(image_progress, filename="progress.png")

      # send the embed
      em = discord.Embed(color=getDiscordMainColor())

      em.set_author(name=f"{ctx.author.display_name} progress: {(progress * 100) :.2f}%", icon_url=ctx.author.display_avatar)

      em.set_image(url="attachment://progress.png")

      await ctx.send(file=file, embed=em)

    @commands.hybrid_command(brief="know the achievements", description="show a list of all obtainable achievements")
    async def achievements(self, ctx : commands.Context):
      # get the connection
      conn = connectionPool.get_connection()
      curs = conn.cursor()
      
      # get the list of achievements
      curs.execute("SELECT * FROM achivements a LEFT JOIN achivements_users au ON a.achivement_id = au.achivement_id AND user_id = (SELECT user_id FROM users WHERE discord_user_id = ?);", [ctx.author.id])
      rows = curs.fetchall()

      LOGGER.log(logging.DEBUG, f"the list of achievements is: \n{rows}")

      # close the connection
      connectionPool.release_connection(conn)

      # create the embed list
      em = discord.Embed(color=getDiscordMainColor())

      em.title = "Achievements"
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

      em.description += "\n\nCompleting all achievements grants access to the host computer keyboard. Type `!help keyboard` for more."

      em.description += "\n\nType `!help <achievement_id>` for hints on how to obtain an achievement."
          
      # send the list
      await ctx.send(embed=em)

      # grant the achievement
      await achievementsUtils.observe_achievement(1, ctx)

    @commands.hybrid_command(brief="how to get an achievement", description="show the description for a given achievement")
    async def achievementinfo(self, ctx : commands.Context, achievement_id : int):
      # get the connection
      conn = connectionPool.get_connection()
      curs = conn.cursor()

      # get the achievement record
      sql = "SELECT * FROM achivements a LEFT JOIN achivements_users au ON a.achivement_id = au.achivement_id AND user_id = (SELECT user_id FROM users WHERE discord_user_id = ?) WHERE a.achivement_id = ?;"

      # TODO: correct names for database fields

      curs.execute(sql, [ctx.author.id, achievement_id])

      row = curs.fetchone()

      LOGGER.log(logging.DEBUG, f"the achievement record is: {row}")

      # release the connection
      connectionPool.release_connection(conn)

      # send the information
      em = discord.Embed(description="", color=getDiscordMainColor())

      if row == None: # if the given achievement id does not exists we informa about it
        em.description = f"{achievement_id} is not a valida achievement id"
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