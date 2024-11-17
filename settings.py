import os
import discord
import sqlite3
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_TOKEN = os.getenv("YOUTUBE_TOKEN")
CODEFORCES_TOKEN = os.getenv("CODEFORCES_TOKEN")

COMMAND_PREFIX = os.getenv("COMMAND_PREFIX")
MAIN_COLOR = os.getenv("MAIN_COLOR")

LOG_LEVEL = os.getenv("LOG_LEVEL")
LOGGER = logging.getLogger('discord.bot')

GIT_REPO = os.getenv("GIT_REPO")

handler = logging.FileHandler("./naota.log")
handler.formatter = logging.Formatter(fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

LOGGER.setLevel(LOG_LEVEL)
LOGGER.addHandler(handler)

# hard-coded values
KUVA_GUILD_ID = 638943159581147137
DEV_GUILD_ID = 1178465444701687878
CHEMS_GUILD_ID = 821940114648334416

# connection string
DB_FILE_PATH = os.getenv("DB_FILE_PATH")