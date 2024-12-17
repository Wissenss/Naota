import io
import math
import logging
from typing import Coroutine

import chess.pgn
import discord
from discord import app_commands
from discord.ext import commands

import cairosvg
import chess
import chess.svg

import connectionPool
from cogs.customCog import CustomCog

from settings import LOGGER
from utils.variousUtils import getDiscordMainColor
from utils import achievementsUtils

PUZZLE_STATUS_UNSOLVED = 0
PUZZLE_STATUS_SOLVED = 1

class DropDownSquare(discord.ui.Select):
    def __init__(self, placeholder : str):

        options = [
            discord.SelectOption(label="a"),
            discord.SelectOption(label="b"),
            discord.SelectOption(label="c"),
            discord.SelectOption(label="d"),
            discord.SelectOption(label="e"),
            discord.SelectOption(label="f"),
            discord.SelectOption(label="g"),
            discord.SelectOption(label="h"),
            discord.SelectOption(label="1"),
            discord.SelectOption(label="2"),
            discord.SelectOption(label="3"),
            discord.SelectOption(label="4"),
            discord.SelectOption(label="5"),
            discord.SelectOption(label="6"),
            discord.SelectOption(label="7"),
            discord.SelectOption(label="8")
        ]

        super().__init__(options=options, placeholder=placeholder, row=0, min_values=2, max_values=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="next")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

class PuzzleView(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.origin_square = DropDownSquare("Or")
        self.final_square = DropDownSquare("Fi")

        self.add_item(self.origin_square)
        self.add_item(self.final_square)

        self.next_button = NextButton(row=0)

        self.add_item(self.next_button)

class ChessCog(CustomCog):
    def __init__(self, bot : commands.Bot):
        super().__init__(bot)

        self.__cog_name__ = "Chess"

        self.current_puzzle_id = self.get_unsolved_puzzle_id()

    def get_unsolved_puzzle_id(self, max_movements = 10):
        conn = connectionPool.get_connection()
        curs = conn.cursor()

        params = [
            PUZZLE_STATUS_UNSOLVED,
            max_movements
        ]

        curs.execute("SELECT * FROM puzzles WHERE status = ? AND no_moves <= ? LIMIT 1;", params)

        raw_data = curs.fetchone()
        
        puzzle_id = raw_data[0]
        fen = raw_data[2]
        moves = raw_data[3]
        status = raw_data[11]

        connectionPool.release_connection(conn)

        return puzzle_id

    def get_current_board(self):
        LOGGER.log(logging.DEBUG, "creating board")

        conn = connectionPool.get_connection()
        curs = conn.cursor()

        curs.execute("SELECT * FROM puzzles WHERE puzzle_id = ?;", [self.current_puzzle_id])

        raw_data = curs.fetchone()

        puzzle_id = raw_data[0]
        fen = raw_data[2]
        moves = raw_data[3]
        no_moves = raw_data[11]
        status = raw_data[12]
        move_progress = raw_data[13]

        LOGGER.log(logging.DEBUG, f"fen: {fen}")
        LOGGER.log(logging.DEBUG, f"moves: {moves}")
        LOGGER.log(logging.DEBUG, f"move_progress: {move_progress}")

        board = chess.Board(fen)

        last_move = ""

        for i in range(move_progress):
            last_move = moves.split(" ")[i] 
            board.push(chess.Move.from_uci(last_move))

        connectionPool.release_connection(conn)

        return (board, puzzle_id, moves, last_move)

    async def send_current_puzzle(self, interaction : discord.Interaction):
        board : chess.Board

        board, puzzle_id, moves, last_move = self.get_current_board()

        colors = {
            "square light" : "#ffffff",
            "square dark" : "#206694",
            "margin" : "#00000000"
        }

        raw_svg = chess.svg.board(board, colors=colors, borders=False, coordinates=True)

        raw_png = cairosvg.svg2png(raw_svg)

        image = io.BytesIO(raw_png) 

        file = discord.File(image, filename="unknown.png")

        em = discord.Embed(title=f"Puzzle #{puzzle_id:05d}", description=f"last move is {last_move}, {"white" if board.turn == chess.WHITE else "black"} to move", color=getDiscordMainColor())

        em.set_image(url="attachment://unknown.png")

        await interaction.response.send_message(file=file, embed=em)

    @app_commands.command(name="puzzle", description="get a puzzle")
    async def puzzle(self, interaction : discord.Interaction):
        await self.cog_before_slash_invoke(interaction)

        await self.send_current_puzzle(interaction)

        return

    @app_commands.command(name="solution", description="give a solution to the current puzzle (in UCI format)")
    async def solution(self, interaction : discord.Interaction, move : str):
        await self.cog_before_slash_invoke(interaction)

        conn = connectionPool.get_connection()
        curs = conn.cursor()

        curs.execute("SELECT * FROM puzzles WHERE puzzle_id = ?;", [self.current_puzzle_id])
        raw_data = curs.fetchone()

        puzzle_id = raw_data[0]
        fen = raw_data[2]
        moves = raw_data[3]
        rating = raw_data[4]
        no_moves = raw_data[11]
        status = raw_data[12]
        move_progress = raw_data[13]

        connectionPool.release_connection(conn)

        em = discord.Embed(title="", description="", color=getDiscordMainColor())

        corrent_move = moves.split(" ")[move_progress]
        LOGGER.log(logging.DEBUG, f"the correct move is: {corrent_move}")

        if move.lower() != corrent_move:
            em.description = f"**{move}** is wrong"
            return await interaction.response.send_message(embed=em)

        if move_progress + 1 < no_moves:
            conn = connectionPool.get_connection()
            curs = conn.cursor()

            curs.execute("UPDATE puzzles SET move_progress = move_progress + 2 WHERE puzzle_id = ?;", [self.current_puzzle_id])

            conn.commit()

            connectionPool.release_connection(conn)

            return await self.send_current_puzzle(interaction)

        conn = connectionPool.get_connection()
        curs = conn.cursor()

        params = [
            PUZZLE_STATUS_SOLVED,
            self.current_puzzle_id
        ]

        curs.execute("UPDATE puzzles SET status = ? WHERE puzzle_id = ?;", params)

        reward = int(rating / 10)

        params = [
            reward,
            interaction.user.id
        ]

        curs.execute("UPDATE users SET puzzles_ranking = puzzles_ranking + ? WHERE discord_user_id = ?;", params)

        conn.commit()

        self.current_puzzle_id = self.get_unsolved_puzzle_id()

        em.description = f"**{move}** is right! **+ {reward}pts**"

        connectionPool.release_connection(conn)

        await interaction.response.send_message(embed=em)

        ctx = await self.bot.get_context(interaction)

        # Ain't that Levy achivement
        await achievementsUtils.observe_achievement(2, ctx)

    @app_commands.command(name="ranking", description="get the global ranking")
    async def ranking(self, interaction : discord.Interaction):
        await self.cog_before_slash_invoke(interaction)

        conn = connectionPool.get_connection()
        curs = conn.cursor()

        curs.execute("SELECT * FROM users ORDER BY puzzles_ranking DESC LIMIT 10;")
        rows = curs.fetchall()

        connectionPool.release_connection(conn)

        em = discord.Embed(title="Puzzles Rankings", description="", color=getDiscordMainColor())

        for i, raw_data in enumerate(rows):
            user_id = raw_data[0]
            discord_user_id = raw_data[1]
            puzzle_ranking = raw_data[2]

            try:
                user = await self.bot.fetch_user(discord_user_id)

                #print(f"discord id: {discord_user_id}")
                #print(f"user object: {user}")

                em.description += f"\n{puzzle_ranking:04d} - {user.display_name}"

            except Exception as e:
                # [TODO] delete the user record if not found
                LOGGER.log(logging.ERROR, f"unhandled exception: {repr(e)}")
            
            
        return await interaction.response.send_message(embed=em)

