import discord
from discord.ext import commands
import connectionPool
from settings import *

def get_default_playlist_id(guild : discord.Guild) -> int:
  conn = connectionPool.get_connection()
  curs = conn.cursor()

  default_playlist_id = 0

  LOGGER.log(logging.DEBUG, f"trying to obtain existing default playlist...")

  # get the default playlist
  sql = "SELECT playlist_id FROM playlists WHERE user_id IS NULL AND guild_id = ?;"

  curs.execute(sql, [guild.id])

  row = curs.fetchone()

  LOGGER.log(logging.DEBUG, f"row: {row}")

  if row:
    default_playlist_id = row[0]
  
  else:
    LOGGER.log(logging.DEBUG, f"non existing default playlist, creating it...")

    # if it doesn't exists create it
    sql = "INSERT INTO playlists(user_id, guild_id) VALUES(NULL, ?);"

    curs.execute(sql, [guild.id])

    conn.commit()

    curs.execute("SELECT last_insert_rowid();")

    row = curs.fetchone()

    LOGGER.log(logging.DEBUG, f"row: {row}")

    default_playlist_id = row[0]

  connectionPool.release_connection(conn)

  return default_playlist_id

def get_youtube_url_from_message(message : discord.Message):
  for word in message.content.split(" "):
    if word.startswith("https://www.youtube.com"):
      return word
  
  return ""

def ensure_guild_record(guild : discord.Guild):
  pass

def get_guild_music_channel_id(guild : discord.Guild):
  LOGGER.log(logging.DEBUG, f"get_guild_music_channel_id called...")

  conn = connectionPool.get_connection()
  curs = conn.cursor()

  sql = "SELECT music_channel_id FROM guilds WHERE discord_guild_id = ?;"

  curs.execute(sql, [guild.id])

  row = curs.fetchone()

  LOGGER.log(logging.DEBUG, f"  row: {row}")

  if not row:
    return None

  channel_id = row[0]

  connectionPool.release_connection(conn)

  return channel_id