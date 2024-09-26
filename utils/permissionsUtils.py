import json
import discord
from discord.ext import commands

"""
the currently supported permissions are the following:

for entire cogs:

Cog_MusicPlayer
Cog_WatchlistCog
Cog_DevCog

for individual commands:

Command_Sync

to determine if a certain permission is valid, it must be included in either
the user permissions, the permissions of a group the user belongs to or the server
permissions from where the request was issued.

"""

PERMISSIONS_FILE = "./permissions.json"
PERMISSIONS = None

# function that gets the permissions data. Also a permissions cog would be a good idea to crud permissions
def get_permissions_json():
  permissions_json = None

  #[TODO] handle the case where permissions file is not found

  with open(PERMISSIONS_FILE) as raw_file:
    raw_data = raw_file.read()
    permissions_json = json.loads(raw_data)

  return permissions_json

def get_group_permissions(group_name : str):
  permissions = PERMISSIONS

  group_permissions = []

  if group_name in permissions["groups"]:
    group_permissions += permissions["groups"][group_name]["permissions"]

  return group_permissions

def get_user_permissions(user_id : int):
  permissions = PERMISSIONS

  user_permissions = []

  if str(user_id) in permissions["users"]:
    user_permissions += permissions["users"][str(user_id)]["permissions"]

  return user_permissions

def get_server_permissions(server_id : int):
  permissions = PERMISSIONS

  server_permissions = []

  if str(server_id) in permissions["servers"]:
    server_permissions += permissions["servers"][str(server_id)]["permissions"]

  return server_permissions

def get_context_permissions(ctx : commands.Context):
  permissions = PERMISSIONS
  
  context_permissions = []

  context_permissions += get_user_permissions(ctx.author.id)
  
  if str(ctx.author.id) in permissions["users"]:
    for group_name in permissions["users"][str(ctx.author.id)]["groups"]:
      context_permissions += get_group_permissions(group_name)

  context_permissions += get_server_permissions(ctx.guild.id)

  print(f"context_permissions: {context_permissions}")
  return context_permissions

def permission_allowed_in_context(ctx : commands.Context, permission : str) -> bool:
  context_permissions = get_context_permissions(ctx)

  return permission in context_permissions

def cog_allowed_in_context(ctx : commands.Context, cog : commands.Cog) -> bool:
  context_permissions = get_context_permissions(ctx)

  cog_permission = f"Cog_{cog.__cog_name__}"

  #print(f"checking permission \"{cog_permission}\" for {ctx.author.name} on guild {ctx.guild.name}")

  return cog_permission in context_permissions

def command_allowed_in_context(ctx : commands.Context, command : commands.Command) -> bool:
  context_permissions = get_context_permissions(ctx)

  command_permission = f"Command_{command.name}"

  #print(f"checking permission \"{command_permission}\" for {ctx.author.name} on guild {ctx.guild.name}")

  return command_permission in context_permissions

if __name__ == "__main__": 
  PERMISSIONS_FILE = "./../permissions.json"

  PERMISSIONS = get_permissions_json()

  stubContext = commands.Context(discord.Message(), bot=None, view=None)

  stubContext.author.id = 334016584093794305
  stubContext.author.name = "wissens"
  stubContext.guild.id = 1178465444701687878

  stubCog = commands.Cog()
  stubCog.__cog_name__ = "Cog_MusicPlayer"

  result = cog_allowed_in_context(stubContext, stubCog)

  print(result)
else:
  PERMISSIONS = get_permissions_json()