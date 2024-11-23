import os
import discord
import sqlite3
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

# API credentials
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_TOKEN = os.getenv("YOUTUBE_TOKEN")
CODEFORCES_TOKEN = os.getenv("CODEFORCES_TOKEN")
TWITTER_KEY = os.getenv("TWITTER_KEY")
TWITTER_SECRET = os.getenv("TWITTER_SECRET")
TWITTER_BEARER = os.getenv("TWITTER_BEARER")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# frontend
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX")
MAIN_COLOR = os.getenv("MAIN_COLOR")

# repo
GIT_REPO = os.getenv("GIT_REPO")

# permissions
PERMISSIONS_FILE_PATH = os.getenv("PERMISSIONS_FILE_PATH")

# logger
LOG_LEVEL = os.getenv("LOG_LEVEL")
LOGGER = logging.getLogger('discord.bot')

handler = logging.FileHandler("./naota.log")
handler.formatter = logging.Formatter(fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

LOGGER.setLevel(LOG_LEVEL)
LOGGER.addHandler(handler)

# hard-coded values
#KUVA_GUILD_ID = 638943159581147137
#DEV_GUILD_ID = 1178465444701687878
#CHEMS_GUILD_ID = 821940114648334416

# database
DB_FILE_PATH = os.getenv("DB_FILE_PATH")