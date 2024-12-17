import discord
from discord.ext import commands

from PIL import Image, ImageDraw

import connectionPool
from settings import *

from utils import permissionsUtils, variousUtils

def create_progress_bar(progress):
  width = 1000
  height = 50

  image = Image.new("RGB", (width, height), (66,69,73))
  
  draw = ImageDraw.Draw(image)

  draw.rectangle([(0,0), (width, height)], fill=(54,57,62))

  draw.rectangle([(0,0), (progress * width, height)], fill="#206694")

  return image

def is_matching_title(title : str, keywords : list[str], minimum_match : int):
  matches = 0

  for keyword in keywords:
    if keyword.lower() in title.lower():
      matches += 1

  return matches >= minimum_match

# this function will progress the achivement if not completed 
# the specific logic to grant or not the achivement is delegated to the caller code of the utility
async def observe_achievement(achivement_id : id, ctx : commands.Context):
  if not permissionsUtils.permission_allowed_in_context(ctx=ctx, permission="Cog_Achivement"):
    return

  LOGGER.log(logging.DEBUG, f"observing achivement...")

  # create the connection
  conn = connectionPool.get_connection()
  curs = conn.cursor()
  
  # get the achivement record
  sql = "SELECT * FROM achivements a LEFT JOIN achivements_users au ON a.achivement_id = au.achivement_id AND user_id = (SELECT user_id FROM users WHERE discord_user_id = ?) WHERE a.achivement_id = ?;"

  curs.execute(sql, [ctx.author.id, achivement_id])

  row = curs.fetchone()

  LOGGER.log(logging.DEBUG, f"the achivement record is: {row}")

  # progress the achivement if not completed 
  a_id = row[0]
  a_name = row[1]
  a_description = row[2]
  au_id = row[3]
  u_id = row[5]

  if au_id == None:
    curs.execute("INSERT INTO achivements_users(achivement_id, user_id, progress) VALUES(?, (SELECT user_id FROM users WHERE discord_user_id = ?), ?)", [a_id, ctx.author.id, 1])

    conn.commit()

    LOGGER.log(logging.INFO, f"achivement completed! (achivement_name: {a_name}) (user_name: {ctx.author.display_name})")

    em = discord.Embed(description=f":trophy: achivement **{a_name}** completed by **{ctx.author.display_name}**", color=variousUtils.getDiscordMainColor())

    await ctx.send(embed=em)

  # release the connection
  connectionPool.release_connection(conn)

if __name__ == "__main__":
  im = create_progress_bar(0.6)

  im.save("output.jpg")