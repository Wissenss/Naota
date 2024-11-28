import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
import git
import time
import datetime
import os
from utils import permissionsUtils, achivementsUtils

from cogs.customCog import CustomCog

import subprocess

import ctypes
import subprocess
from ctypes import wintypes

# Load necessary Windows libraries
wtsapi32 = ctypes.WinDLL('wtsapi32')
kernel32 = ctypes.WinDLL('kernel32')

# Constants
WTS_CURRENT_SERVER_HANDLE = None

# Define functions and constants
def run_program_in_session(session_id, program_path):
    """Run a program in a specified session."""
    # Query the user token for the session
    token = wintypes.HANDLE()
    if not wtsapi32.WTSQueryUserToken(session_id, ctypes.byref(token)):
        raise ctypes.WinError()

    # Duplicate the token to create a primary token
    duplicated_token = wintypes.HANDLE()
    if not kernel32.DuplicateTokenEx(
        token,
        0x10000000,  # MAXIMUM_ALLOWED
        None,
        2,  # SecurityImpersonation
        1,  # TokenPrimary
        ctypes.byref(duplicated_token),
    ):
        raise ctypes.WinError()

    # Setup process startup info
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_SHOW

    # Launch the process in the target session
    subprocess.Popen(
        program_path,
        startupinfo=si,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        close_fds=True,
        token=duplicated_token,
    )

    print(f"Program launched in session {session_id}.")

class KeyboardCog(CustomCog):
  def __init__(self, bot : commands.Bot):
    super().__init__(bot)

    self.__cog_name__ = "Keyboard"

  @commands.hybrid_command(brief="press space", description="press the spacebar")
  async def space(self, ctx : commands.Context):
    subprocess.Popen("python C:\\Users\\Leo\\Dev\\Naota\\cli.py space", start_new_session=True)

    #run_program_in_session(1, "python C:\\Users\\Leo\\Dev\\Naota\\cli.py space")