from typing import Any
import discord
from discord.ext import commands

from settings import COMMAND_PREFIX

from variousUtils import getDiscordMainColor

""" 
I create this helper functions to centralize the help message creation. This are then called from
both the CustomHelpCommand class and the CustomHelpSlashCommand. Not too elegent but good enough for now  
"""

def get_help_embed(mapping):
  desciption_ = ""
  for cog, cmds in mapping.items():
    
    if cog:
      desciption_ += f"\n\n__**{cog.qualified_name}**__"
    else:
      desciption_ += "\n\n__**No Category**__"

    for command in cmds:
      if command.hidden: 
        continue

      desciption_ += f"\n**{COMMAND_PREFIX}{command.qualified_name}: ** {command.brief}"

  desciption_ += f"\n\nType `{COMMAND_PREFIX}help command_name` for more info on a command. You can also type `{COMMAND_PREFIX}help category_name` for more info on a category"

  em = discord.Embed(title="", description=desciption_, color=getDiscordMainColor())

  return em

def get_command_help_embed(command : commands.Command):
  em = discord.Embed(color=getDiscordMainColor())

  em.title = f"{command.full_parent_name} {command.name}"

  em.description = f"{command.description}"

  if command.clean_params:
    em.description += "\n\n__**Arguments**__"

  for param_name in command.clean_params:
    parameter = command.clean_params[param_name]
    
    em.description += f"\n{parameter.name}"

    if parameter.required:
      em.description += " (required) "

  return em

def get_group_help_embed(group : commands.Group):
  em = get_command_help_embed(group)

  if group.commands:
    em.description += "\n\n__**SubCommands**__"

    for command in group.commands:
      em.description += f"\n{command.name}"

  return em

def get_cog_help_embed(cog : commands.Cog):
  description_ = f"{cog.description}"

  description_ += "\n\n __**Commands**__"

  for command in cog.get_commands():
    description_ += f"\n **{COMMAND_PREFIX}{command.qualified_name}: ** {command.brief}"

  em = discord.Embed(title=f"", description=description_, color=getDiscordMainColor())

class CustomHelpCommand(commands.HelpCommand):
  def __init__(self):
    super().__init__()

    self.command_attrs["brief"] = "show this message"

    self.command_attrs["description"] = f"show al list of commands and its description"
    self.command_attrs["description"] += self.help_usage_str

  async def send_bot_help(self, mapping):
    em = get_help_embed(mapping)

    channel = self.get_destination()
    await channel.send(embed=em)

  async def send_command_help(self, command):
    if command.hidden: 
      return

    em = get_command_help_embed(command)

    channel = self.get_destination()
    await channel.send(embed=em)

  async def send_group_help(self, group):
    if group.hidden:
      return
    
    em = get_group_help_embed(group)

    channel = self.get_destination()
    await channel.send(embed=em)

  async def send_cog_help(self, cog: commands.Cog):
    
    em = get_cog_help_embed(cog)

    channel = self.get_destination()
    await channel.send(embed=em)