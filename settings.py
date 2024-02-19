import os
import discord
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_TOKEN = os.getenv("YOUTUBE_TOKEN")
CODEFORCES_TOKEN = os.getenv("CODEFORCES_TOKEN")

COMMAND_PREFIX = os.getenv("COMMAND_PREFIX")
MAIN_COLOR = os.getenv("MAIN_COLOR")

LOGGER = logging.getLogger('discord')

handler = logging.FileHandler("./naota.log")
handler.formatter = logging.Formatter(fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
#handler.formatter = logging.Formatter(style=logging._FormatStyle.)

LOGGER.addHandler(handler)