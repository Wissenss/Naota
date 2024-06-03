import discord

from settings import *

def getDiscordMainColor():
  if MAIN_COLOR == "" or MAIN_COLOR == "random":
    return discord.Color.random()

  if MAIN_COLOR == "default": return discord.Color.default()
  if MAIN_COLOR == "teal": return discord.Color.teal()
  if MAIN_COLOR == "dark_teal": return discord.Color.teal()
  if MAIN_COLOR == "brand_green": return discord.Color.brand_green()
  if MAIN_COLOR == "green": return discord.Color.green()
  if MAIN_COLOR == "dark_green": return discord.Color.dark_green()
  if MAIN_COLOR == "blue": return discord.Color.blue()
  if MAIN_COLOR == "dark_blue": return discord.Color.dark_blue()
  if MAIN_COLOR == "purple": return discord.Color.purple()
  if MAIN_COLOR == "dark_purple": return discord.Color.dark_purple()
  if MAIN_COLOR == "magenta": return discord.Color.magenta()
  if MAIN_COLOR == "dark_magenta": return discord.Color.dark_magenta()
  if MAIN_COLOR == "gold": return discord.Color.gold
  if MAIN_COLOR == "dark_gold": return discord.Color
  if MAIN_COLOR == "orange": return discord.Color.orange
  if MAIN_COLOR == "dark_orange": return discord.Color.dark_orange
  if MAIN_COLOR == "brand_red": return discord.Color.brand_red()
  if MAIN_COLOR == "red": return discord.Color.red()
  if MAIN_COLOR == "dark_red": return discord.Color.dark_red()
  if MAIN_COLOR == "lighter_grey": return discord.Color.lighter_grey
  if MAIN_COLOR == "dark_grey": return discord.Color.dark_grey()
  if MAIN_COLOR == "light_grey": return discord.Color.light_grey()
  if MAIN_COLOR == "darker_grey": return discord.Color.darker_grey()
  if MAIN_COLOR == "og_blurple": return discord.Color.og_blurple()
  if MAIN_COLOR == "blurple": return discord.Color.blurple()
  if MAIN_COLOR == "dark_theme": return discord.Color.dark_theme()
  if MAIN_COLOR == "fuchsia": return discord.Color.fuchsia()
  if MAIN_COLOR == "yellow": return discord.Color.yellow()
  if MAIN_COLOR == "dark_embed": return discord.Color.dark_embed()
  if MAIN_COLOR == "light_embed": return discord.Color.light_embed()
  if MAIN_COLOR == "pink": return discord.Color.pink()
  
  return discord.Color.from_str(MAIN_COLOR)