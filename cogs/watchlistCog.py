import sqlite3
import logging
from settings import *
from utils.variousUtils import getDiscordMainColor
import connectionPool
import discord
from discord import app_commands
from discord.ext import commands
from utils import permissionsUtils

WATCHLIST_ITEM_STATUS_PLAN_TO_WATCH = 0
WATCHLIST_ITEM_STATUS_WATCHING = 1
WATCHLIST_ITEM_STATUS_ON_HOLD = 2
WATCHLIST_ITEM_STATUS_COMPLETED = 3,
WATCHLIST_ITEM_STATUS_DROPPED = 4

class WatchlistModal(discord.ui.Modal, title="Watchlist"):
  label_name = discord.ui.TextInput(label="Name", style=discord.TextStyle.short, placeholder="\"nicho\" playlist")


class WatchlistCog(commands.Cog):
  "Keep track of movies and shows"

  watchlist_group = app_commands.Group(name="watchlist", description="operations for watchlists")
  watchitem_group = app_commands.Group(name="watchitme", description="operations for items inside watchlists")

  def __init__(self, bot : commands.Bot):
    self.bot = bot

    self.__cog_name__ = "Watchlist"
  
  async def cog_before_invoke(self, ctx: commands.Context):
    LOGGER.log(logging.INFO, f"{ctx.command.name} called (USER ID {ctx.author.id}) (GUILD ID: {ctx.guild.id})")

  async def cog_check(self, ctx: commands.Context) -> bool:
    return permissionsUtils.cog_allowed_in_context(ctx, self)
  
  def __watchlist_item_status_to_tag(self, watchlist_item_status : int):
    if watchlist_item_status == WATCHLIST_ITEM_STATUS_PLAN_TO_WATCH: return "plan to watch"
    if watchlist_item_status == WATCHLIST_ITEM_STATUS_WATCHING: return "watching"
    if watchlist_item_status == WATCHLIST_ITEM_STATUS_ON_HOLD: return "on hold"
    if watchlist_item_status == WATCHLIST_ITEM_STATUS_COMPLETED: return "completed"
    if watchlist_item_status == WATCHLIST_ITEM_STATUS_DROPPED: return "dropped"

    return "unknown"

  async def __get_default_watchlist(self, ctx : commands.Context) -> int:
    default_watchlist_name = "default"
    
    try:
      conn = connection.get_connection()
      curs = conn.cursor()

      LOGGER.log(logging.DEBUG, f"searching default watchlist...")

      params = [ctx.guild.id, default_watchlist_name]

      curs.execute("SELECT watchlist_id FROM watchlists WHERE guild_id = ? AND watchlist_name = ?;", params)

      watchlist_id = curs.fetchone()[0]

      if watchlist_id:
        LOGGER.log(logging.DEBUG, f"default watchlist found, retreiving id: {watchlist_id}")

        return watchlist_id
      
      else:
        LOGGER.log(logging.DEBUG, f"default watchlis NOT found, creating...")

        params = [default_watchlist_name, ctx.guild.id, ctx.author.id]

        curs.execute("INSERT INTO watchlists(watchlist_name, guild_id, owner_id) VALUES(?,?,?)", params)

        watchlist_id = curs.lastrowid

        LOGGER.log(logging.DEBUG, f"default watchlist created. watchlist_id: {watchlist_id}")

        conn.commit()

        return watchlist_id

    except Exception as e:

      LOGGER.log(logging.ERROR, f"unhandled exception on __get_default_watchlist: {repr(e)}")
      
      return 0
    
    finally:
      connection.release_connection(conn)

  async def __get_currently_watching_item(watchlist_id : int):
    try:
      conn = connection.get_connection()
      curs = conn.cursor()

      params = [WATCHLIST_ITEM_STATUS_WATCHING, watchlist_id]

      curs.execute("SELECT watchlist_item_id FROM watchlist_items WHERE status = ? AND watchlist_id = ? LIMIT 1", params)

      record = curs.fetchone()

      if record:
        return record[0] 

    except Exception as e:
      LOGGER.log(logging.ERROR, f"unhandled exception on __get_currently_watching_item: {repr(e)}")
    
    finally:
      connection.release_connection(conn)

    return 0

  # @commands.hybrid_command()
  # async def watchlist_show(self, ctx : commands.Context, watchlist_id : int = 0):
  #   em = discord.Embed(title="Watchlist", description="", color=getDiscordMainColor())

  #   try:      
  #     if watchlist_id == 0:
  #       LOGGER.log(logging.DEBUG, "No watchlist specified, assuming default")
  #       watchlist_id = await self.__get_default_watchlist(ctx)
  #       LOGGER.log(logging.DEBUG, f"default watchlis_id: {watchlist_id}")

  #     conn = connection.get_connection()

  #     curs = conn.execute("SELECT * FROM watchlist_items WHERE watchlist_id = ?;", [watchlist_id])

  #     em.description = ""

  #     for i, item in enumerate(curs.fetchall()):
  #       status_str = self.__watchlist_item_status_to_tag(item[4])
  #       em.description += f"\n{item[0]}. {item[2]} ({item[7]}/{item[5]}) ({status_str})" 

  #   except Exception as e:
  #     em.title = ""
  #     em.description = f"unhandled exception on {ctx.command.name}: {repr(e)}"
  #     em.color = discord.Color.red()

  #     LOGGER.log(logging.ERROR, em.description)

  #   finally:
  #     connection.release_connection(conn)

  #   await ctx.send(embed=em)

  # @commands.hybrid_command()
  # async def watching(self, ctx : commands.Context):
  #   em = discord.Embed(title="", description="", color=getDiscordMainColor())

  #   try:
  #     conn = connection.get_connection()
  #     curs = conn.cursor()

  #     watchlistId = await self.__get_default_watchlist(ctx)

  #     params = [WATCHLIST_ITEM_STATUS_WATCHING, watchlistId]

  #     curs.execute("SELECT * FROM watchlist_items WHERE status = ? AND watchlist_id = ? LIMIT 1", params)

  #     record = curs.fetchone() 

  #     if record:
  #       em.title = record[2]

  #       em.description += f"\ncompleted: {(record[7]/record[5]):.0%} ({record[7]}/{record[5]})"
  #       em.description += f"\nremaining watchtime: {record[6] * (record[5] - record[7])}min"

  #   except Exception as e:
  #     em.title = ""
  #     em.description = f"unhandled exception on {ctx.command.name}: {repr(e)}"
  #     em.color = discord.Color.red()

  #     LOGGER.log(logging.ERROR, em.description)

  #   finally:
  #     connection.release_connection(conn)

  #   await ctx.send(embed=em)

  # @commands.hybrid_command()
  # async def watched(self, ctx : commands.Context):
  #   em = discord.Embed()
    
  #   try:
  #     conn = connection.get_connection()
  #     curs = conn.cursor()

  #     watchlist_id = await self.__get_default_watchlist(ctx)

  #     params = [WATCHLIST_ITEM_STATUS_WATCHING, watchlist_id]

  #     curs.execute("UPDATE watchlist_items SET current_episode = current_episode + 1 WHERE status = ? AND watchlist_id = ?", params)

  #     curs.execute("SELECT * from watchlist_items WHERE status = ? and watchlist_id")

  #     conn.commit()

  #     await self.watching(ctx)

  #   except Exception as e:
  #     em.title = ""
  #     em.description = f"unhandled exception on {ctx.command.name}: {repr(e)}"
  #     em.color = discord.Color.red()

  #     LOGGER.log(logging.ERROR, em.description)
    
  #     await ctx.send(embed=em)

  #   finally:
  #     connection.release_connection(conn)

  # @commands.hybrid_command()
  # async def watchlist_add(self, ctx : commands.Context, title : str, episodes : int, duration : int):
  #   em = discord.Embed()

  #   try:
  #     conn = connection.get_connection()
  #     curs = conn.cursor()

  #     watchlist_id = await self.__get_default_watchlist(ctx)

  #     params = [watchlist_id, title, ctx.guild.id, WATCHLIST_ITEM_STATUS_WATCHING, episodes, duration, 0]

  #     curs.execute("INSERT INTO watchlist_items(watchlist_id, name, author_id, status, total_episodes, episode_duration, current_episode) VALUES (?, ?, ?, ?, ?, ?, ?)", params)

  #     conn.commit()

  #     await self.watchlist_show(ctx)

  #   except Exception as e:
  #     em.title = ""
  #     em.description = f"unhandled exception on {ctx.command.name}: {repr(e)}"
  #     em.color = discord.Color.red()

  #     LOGGER.log(logging.ERROR, em.description)
    
  #     await ctx.send(embed=em)

  #   finally:
  #     connection.release_connection(conn)

  # WATCHLISTS

  @watchlist_group.command(name="show", description="show all items inside the watchlist")
  async def watchlist_show(self, interaction : discord.Interaction, watchlist_id : int):
    em = discord.Embed(title="", description="", color=getDiscordMainColor())

    conn = connectionPool.get_connection()
    curs = conn.cursor()

    curs.execute("SELECT * FROM watchlists WHERE watchlist_id = ?", [watchlist_id])
    row_data = curs.fetchone()

    watchlist_name = row_data[1]
    
    em.title = f"Watchlist #{watchlist_id}: {watchlist_name}"

    curs.execute("SELECT * FROM watchlist_items WHERE watchlist_id = ? ORDER BY watchlist_item_id DESC;", [watchlist_id])
    rows_list = curs.fetchall()

    for row in rows_list:
      watchlist_item_id = row[0]
      watchlist_id = row[1]
      name = row[2]
      author_id = row[3]

      em.description += f"\n{watchlist_item_id} - {name}"

    connectionPool.release_connection(conn)

  @watchlist_group.command(name="list", description="show a list of all existing watchlists for current server")
  async def watchlist_list(self, interaction : discord.Interaction):
    em = discord.Embed(title="Watchlists", description="", color=getDiscordMainColor())

    conn = connectionPool.get_connection()

    try:
      curs = conn.cursor()
      curs.execute("SELECT * FROM watchlists WHERE guild_id = ?;", [interaction.guild_id])
      rows_list = curs.fetchall()

      for row in rows_list:
        watchlist_id = row[0]
        name = row[1]

        em.description += f"\n{watchlist_id} - {name}"
    
      interaction.response.send_message(embed=em)
    
    except Exception as e:
      pass
    
    finally:
      connectionPool.release_connection(conn)

  @watchlist_group.command(name="add", description="create a new watchlist")
  async def watchlist_add(self, interaction : discord.Interaction):
    pass
  
  @watchlist_group.command(name="edit", description="edita a watchlist")
  async def watchlist_edit(self, interaction : discord.Interaction):
    pass

  # WATCHLIST ITEMS 

  @watchitem_group.command(name="show", description="show details for the give watchlist item")
  async def watchitem_show(self, interaction : discord.Interaction):
    pass

  @watchitem_group.command(name="watched", description="increments watch count by one")
  async def watchitem_watched(self, interaction : discord.Interaction, watchitem_id : int):
    pass

  @watchitem_group.command(name="add", description="create an item in given watchlist")
  async def watchitem_add(self, interaction : discord.Interaction, watchlist_id : int):
    pass

  @watchitem_group.command(name="edit", description="edit a watchlist item information")
  async def watchitem_edit(self, interaction : discord.Interaction, watchitem_id : int):
    pass