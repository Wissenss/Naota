import sqlite3
import logging
from settings import *
from utils.variousUtils import getDiscordMainColor
import connectionPool
import discord
from discord import app_commands
from discord.ext import commands
from utils import permissionsUtils
from cogs.customCog import CustomCog

WATCHLIST_ITEM_STATUS_PLAN_TO_WATCH = 0
WATCHLIST_ITEM_STATUS_WATCHING = 1
WATCHLIST_ITEM_STATUS_ON_HOLD = 2
WATCHLIST_ITEM_STATUS_COMPLETED = 3,
WATCHLIST_ITEM_STATUS_DROPPED = 4

def watchlist_item_status_to_tag(watchlist_item_status : int):
  if watchlist_item_status == WATCHLIST_ITEM_STATUS_PLAN_TO_WATCH: return "plan to watch"
  if watchlist_item_status == WATCHLIST_ITEM_STATUS_WATCHING: return "watching"
  if watchlist_item_status == WATCHLIST_ITEM_STATUS_ON_HOLD: return "on hold"
  if watchlist_item_status == WATCHLIST_ITEM_STATUS_COMPLETED: return "completed"
  if watchlist_item_status == WATCHLIST_ITEM_STATUS_DROPPED: return "dropped"

  return "unknown"

def create_watchlist_embed(interaction : discord.Interaction, watchlist_id : int) -> discord.Embed:
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

    return em

class WatchlistModal(discord.ui.Modal, title="Add Watchlist"):

  def __init__(self, interaction : discord.Interaction, watchlist_id : int = 0 ):
    super().__init__()

    self.label_name = discord.ui.TextInput(label="Name", style=discord.TextStyle.short, placeholder="\"nicho\" name")

    self.is_creation = True
    self.watchlist_id = watchlist_id
    
    if watchlist_id > 0:
      self.fill_watchlist_info(interaction, watchlist_id)
      self.is_creation = False
      self.title = "Edit watchlist"

    self.add_item(self.label_name)
    
  def fill_watchlist_info(self, interaction : discord.Interaction, watchlist_id : int):
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    curs.execute("SELECT * FROM watchlists WHERE watchlist_id = ?;", [watchlist_id])
    row_data = curs.fetchone()

    print(f"row data: {row_data}")

    watchlist_name = row_data[1]

    self.label_name.default = watchlist_name 

    connectionPool.release_connection(conn)

  async def on_submit(self, interaction: discord.Interaction):
    conn = connectionPool.get_connection()
    curs = conn.cursor()
    
    if self.is_creation:
      params = [
        self.label_name.value,
        interaction.guild.id,
        interaction.user.id
      ]

      curs.execute("INSERT INTO watchlists(watchlist_name, guild_id, owner_id) VALUES(?, ?, ?)", params)

      self.watchlist_id = curs.lastrowid

    else:
      params = [
        self.label_name.value,
        self.watchlist_id
      ]

      curs.execute("UPDATE watchlists SET watchlist_name = ? WHERE watchlist_id = ?", params)

    conn.commit()

    connectionPool.release_connection(conn)

    em = create_watchlist_embed(interaction, self.watchlist_id)

    return await interaction.response.send_message(embed=em)

def create_watchitem_embed(interaction : discord.Interaction, watchitem_id : int) -> discord.Embed:
  em = discord.Embed(title="", description="", color=getDiscordMainColor())

  conn = connectionPool.get_connection()
  curs = conn.cursor()

  curs.execute("SELECT * FROM watchlist_items WHERE watchlist_item_id = ?", [watchitem_id])

  raw_data = curs.fetchone()

  name = raw_data[2]
  status = raw_data[4]
  total_episodes = raw_data[5]
  episode_duration = raw_data[6]
  current_episode = raw_data[7]

  em.description += f"\n**Name: **{name}"
  em.description += f"\n**Status: **{watchlist_item_status_to_tag(status)}"
  em.description += f"\nProgress: {(current_episode/total_episodes):.0%} ({current_episode}/{total_episodes})"
  em.description += f"\nRemaining: {(total_episodes - current_episode) * episode_duration}min"

  return em

class WatchitemModal(discord.ui.Modal, title="Add watchitem"):
  def __init__(self, interaction : discord.Interaction, watchitem_id : int = 0, watchlist_id : int = 0):
    super().__init__()

    self.watchlist_id = watchlist_id
    self.watchitem_id = watchitem_id
    self.is_creation = True

    self.input_name = discord.ui.TextInput(label="Name", style=discord.TextStyle.short, placeholder="\"nicho\" name")
    self.input_current_episode = discord.ui.TextInput(label="Current episode", style=discord.TextStyle.short, placeholder="10")
    self.input_total_episodes = discord.ui.TextInput(label="Total episodes", style=discord.TextStyle.short, placeholder="24")
    self.input_episode_duration = discord.ui.TextInput(label="Episode duration", style=discord.TextStyle.short, placeholder="20")

    if watchitem_id > 0:
      self.fill_watchitem_info(interaction, watchitem_id)
      self.title = "Edit watchitem"
      self.is_creation = False

    self.add_item(self.input_name)
    self.add_item(self.input_current_episode)
    self.add_item(self.input_total_episodes)
    self.add_item(self.input_episode_duration)

  def set_input_selection(self, selected_option : int):
    for option in self.input_status.options:
      if option.value == f"{selected_option}":
        option.default = True
      else:
        option.default = False

  def fill_watchitem_info(self, interaction : discord.Interaction, watchitem_id : int):
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    curs.execute("SELECT * FROM watchlist_items WHERE watchlist_item_id = ?;", [watchitem_id])

    raw_data = curs.fetchone()

    name = raw_data[2]
    status = raw_data[4]
    total_episodes = raw_data[5]
    episode_duration = raw_data[6]
    current_episode = raw_data[7]

    self.input_name.default = name
    self.input_current_episode.default = current_episode
    self.input_total_episodes.default = total_episodes
    self.input_episode_duration.default = episode_duration

    connectionPool.release_connection(conn)

  async def on_submit(self, interaction: discord.Interaction):
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    if self.is_creation:
      params = [
        self.watchlist_id,
        self.input_name.value,
        interaction.user.id,
        WATCHLIST_ITEM_STATUS_PLAN_TO_WATCH,
        int(self.input_total_episodes.value),
        int(self.input_episode_duration.value),
        int(self.input_current_episode.value)
      ]

      curs.execute("INSERT INTO watchlist_items(watchlist_id, name, author_id, status, total_episodes, episode_duration, current_episode) VALUES(?, ?, ?, ?, ?, ?, ?);", params)

      self.watchitem_id = curs.lastrowid

    else:
      params = [
        self.input_name.value,
        int(self.input_total_episodes.value),
        int(self.input_episode_duration.value),
        int(self.input_current_episode.value),
        self.watchitem_id
      ]

      curs.execute("UPDATE watchlist_items SET name = ?, total_episodes = ?, episode_duration = ?, current_episode = ? WHERE watchlist_item_id = ?;", params)

    conn.commit()

    connectionPool.release_connection(conn)
    
    em = create_watchitem_embed(interaction, self.watchitem_id)

    return await interaction.response.send_message(embed=em)
    #return await super().on_submit(interaction)

class WatchlistCog(CustomCog):
  "Keep track of movies and shows"

  watchlist_group = app_commands.Group(name="watchlist", description="operations for watchlists")
  watchitem_group = app_commands.Group(name="watchlist_item", description="operations for items inside watchlists")

  def __init__(self, bot : commands.Bot):
    self.bot = bot

    self.__cog_name__ = "Watchlist"

  def get_default_watchlist_id(self, interaction : discord.Interaction):
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    curs.execute("SELECT * FROM watchlists WHERE guild_id = ? ORDER BY watchlist_id ASC LIMIT 1", [interaction.guild.id])
    raw_data = curs.fetchone()

    watchlist_id = raw_data[0]

    connectionPool.release_connection(conn)

    return watchlist_id

  def get_watching_item_id(self, interaction :discord.Interaction, watchlist_id : int):
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    params = [
      watchlist_id,
      WATCHLIST_ITEM_STATUS_WATCHING
    ]

    curs.execute("SELECT * FROM watchlist_items WHERE watchlist_id = ? AND status = ? ORDER BY watchlist_item_id ASC LIMIT 1", params)
    raw_data = curs.fetchone()

    watchitem_id = raw_data[0]

    connectionPool.release_connection(conn)

    return watchitem_id
  
  @app_commands.command(name="watching", description="get what you are currentley watching")
  async def watching(self, interaction : discord.Interaction):
    watchlist_id = self.get_default_watchlist_id(interaction)

    watchitem_id = self.get_watching_item_id(interaction, watchlist_id)

    em = create_watchitem_embed(interaction, watchitem_id)

    return await interaction.response.send_message(embed=em)

  @watchlist_group.command(name="show", description="show all items inside the watchlist")
  async def watchlist_show(self, interaction : discord.Interaction, watchlist_id : int):
    em = create_watchlist_embed(interaction, watchlist_id)

    return await interaction.response.send_message(embed=em)

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
    
      await interaction.response.send_message(embed=em)
    
    except Exception as e:
      await self.log_and_show_exception(e, interaction)
    
    finally:
      connectionPool.release_connection(conn)

  @watchlist_group.command(name="add", description="create a new watchlist")
  async def watchlist_add(self, interaction : discord.Interaction):
    modal = WatchlistModal(interaction)

    await interaction.response.send_modal(modal)
  
  @watchlist_group.command(name="edit", description="edita a watchlist")
  async def watchlist_edit(self, interaction : discord.Interaction, watchlist_id : int):
    modal = WatchlistModal(interaction, watchlist_id)

    await interaction.response.send_modal(modal)
  
  # WATCHLIST ITEMS 

  @watchitem_group.command(name="show", description="show details for the give watchlist item")
  async def watchitem_show(self, interaction : discord.Interaction, watchitem_id : int):
    em = create_watchitem_embed(interaction, watchitem_id)

    return await interaction.response.send_message(embed=em)

  @watchitem_group.command(name="watched", description="increments watch count by one")
  async def watchitem_watched(self, interaction : discord.Interaction, watchitem_id : int):
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    curs.execute("UPDATE watchlist_items SET current_episode = current_episode + 1 WHERE watchlist_item_id = ?", watchitem_id)

    conn.commit()

    connectionPool.release_connection(conn)

    em = create_watchitem_embed(watchitem_id)

    return await interaction.response.send_message(embed=em)

  @watchitem_group.command(name="add", description="create an item in given watchlist")
  async def watchitem_add(self, interaction : discord.Interaction, watchlist_id : int):
    modal = WatchitemModal(interaction, 0, watchlist_id)

    return await interaction.response.send_modal(modal)

  @watchitem_group.command(name="edit", description="edit a watchlist item information")
  async def watchitem_edit(self, interaction : discord.Interaction, watchitem_id : int):
    modal = WatchitemModal(interaction, watchitem_id)

    return await interaction.response.send_modal(modal)
  
  @watchitem_group.command(name="status", description="set the item status")
  async def watchitem_status(self, interaction : discord.Interaction, watchitem_id : int = 0, status : int = 1):
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    curs.execute("UPDATE watchlist_items SET status = ? WHERE watchlist_item_id = ?", [status, watchitem_id])

    conn.execute()

    connectionPool.release_connection(conn)

    em = create_watchitem_embed(interaction, watchitem_id)

    return interaction.response.send_message(embed=em)