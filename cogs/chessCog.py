import io

import chess.pgn
import discord
from discord import app_commands
from discord.ext import commands

import cairosvg
import chess
import chess.svg

from cogs.customCog import CustomCog

import settings
from utils.variousUtils import getDiscordMainColor

"""
/puzzle
/solution <theActualSolution>
/ranking
"""

class ChessCog(CustomCog):
    def __init__(self, bot : commands.Bot):
        super().__init__(bot)

        self.__cog_name__ = "Chess"

    @app_commands.command(name="puzzle", description="get a puzzle")
    async def puzzle(self, interaction : discord.Interaction):
        fen = "4k3/R7/8/1R6/8/8/8/1K6"
        
        testBoard = chess.Board(fen)

        colors = {
            "square light" : "#ffffff",
            "square dark" : "#206694",
            "margin" : "#00000000"
        }

        raw_svg = chess.svg.board(testBoard, colors=colors, borders=False, coordinates=True)

        raw_png = cairosvg.svg2png(raw_svg)

        image = io.BytesIO(raw_png) 

        file = discord.File(image, filename="unknown.png")

        em = discord.Embed(title="Puzzle #0000", description="white to move", color=getDiscordMainColor())

        em.set_image(url="attachment://unknown.png")

        await interaction.response.send_message(file=file, embed=em)

