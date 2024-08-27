import json
import discord
from discord.ext import commands

"""
the currently supported permissions are the following:

for entire cogs:

Cog_MusicPlayer
Cog_KuvaCog
Cog_ChemsCog

for individual commands:

music_comments_get

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

def permission_allowed_in_context(ctx : commands.Context, permission : str):
  context_permissions = get_context_permissions(ctx)

  return permission in context_permissions

def cog_allowed_in_context(ctx : commands.Context, cog : commands.Cog):
  context_permissions = get_context_permissions(ctx)

  cog_permission = f"Cog_{cog.__cog_name__}"

  print(f"checking cog permission: {cog_permission}")

  return cog_permission in context_permissions

"""
def get_member_permissions(member_id : str) -> list[str]:
  with open("./data.json") as raw_file:
    raw_data = raw_file.read()
    data = json.loads(raw_data)

    user_permissions = []

    if member_id in data["users"]:
      user_permissions = data["users"][member_id]["permissions"]

      for group in data["users"][member_id]["groups"]:
        if group in data["groups"]:
          user_permissions += data["groups"][group]["permissions"]

    return user_permissions

def member_has_permision(ctx : commands.Context, permission : str) -> bool:
  member_id = ctx.author.id
  
  user_permissions = get_member_permissions(member_id)

  return permission in user_permissions

def member_cog_allowed(ctx : commands.Context, cog : commands.Cog) -> bool:
  user_permissions = get_member_permissions()

  print(f"checking permissions for cog: {cog.__cog_name__}")

  return cog.__cog_name__ in user_permissions

"""

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