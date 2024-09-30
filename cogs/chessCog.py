import io
import math
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

import settings
from utils.variousUtils import getDiscordMainColor

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
        print("wololo button callback")
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

    def get_unsolved_puzzle_id(self):
        conn = connectionPool.get_connection()
        curs = conn.cursor()

        params = [
            PUZZLE_STATUS_UNSOLVED,
            2
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
        conn = connectionPool.get_connection()
        curs = conn.cursor()

        curs.execute("SELECT * FROM puzzles WHERE puzzle_id = ?;", [self.current_puzzle_id])

        raw_data = curs.fetchone()

        puzzle_id = raw_data[0]
        fen = raw_data[2]
        moves = raw_data[3]
        status = raw_data[11]

        print(f"fen is: {fen}")
        print(f"moves are: {moves}")

        board = chess.Board(fen)

        board.push(chess.Move.from_uci(moves.split(" ")[0]))

        connectionPool.release_connection(conn)

        return (board, puzzle_id, moves)
        
    @app_commands.command(name="puzzle", description="get a puzzle")
    async def puzzle(self, interaction : discord.Interaction):
        await self.cog_before_slash_invoke(interaction)

        board : chess.Board

        board, puzzle_id, moves = self.get_current_board()

        colors = {
            "square light" : "#ffffff",
            "square dark" : "#206694",
            "margin" : "#00000000"
        }

        raw_svg = chess.svg.board(board, colors=colors, borders=False, coordinates=True)

        raw_png = cairosvg.svg2png(raw_svg)

        image = io.BytesIO(raw_png) 

        file = discord.File(image, filename="unknown.png")

        em = discord.Embed(title=f"Puzzle #{puzzle_id:05d}", description=f"{"white" if board.turn == chess.WHITE else "black"} to move", color=getDiscordMainColor())

        em.set_image(url="attachment://unknown.png")

        #vi = PuzzleView()

        await interaction.response.send_message(file=file, embed=em)

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
        status = raw_data[11]

        connectionPool.release_connection(conn)

        em = discord.Embed(title="", description="", color=getDiscordMainColor())

        print(f"the correct move is: {move.split(" ")[-1]}")

        if move.lower() != moves.split(" ")[-1]:
            em.description = f"**{move}** is wrong"
            return await interaction.response.send_message(embed=em)
        
        conn = connectionPool.get_connection()
        curs = conn.cursor()

        params = [
            PUZZLE_STATUS_SOLVED,
            self.current_puzzle_id
        ]

        curs.execute("UPDATE puzzles SET status = ? WHERE puzzle_id = ?;", params)

        curs.execute("UPDATE users SET puzzles_ranking = puzzles_ranking + 10 WHERE discord_user_id = ?", [interaction.user.id])

        conn.commit()

        self.current_puzzle_id = self.get_unsolved_puzzle_id()

        connectionPool.release_connection(conn)

        em.description = f"**{move}** is right!"

        return await interaction.response.send_message(embed=em)

    @app_commands.command(name="ranking", description="get the global ranking")
    async def ranking(self, interaction : discord.Interaction):
        await self.cog_before_slash_invoke(interaction)

        conn = connectionPool.get_connection()
        curs = conn.cursor()

        curs.execute("SELECT * FROM users ORDER BY puzzles_ranking LIMIT 10;")
        rows = curs.fetchall()

        connectionPool.release_connection(conn)

        em = discord.Embed(title="Puzzles Rankings", description="", color=getDiscordMainColor())

        for i, raw_data in enumerate(rows):
            user_id = raw_data[0]
            discord_user_id = raw_data[1]
            puzzle_ranking = raw_data[2]

            try:
                user = await self.bot.fetch_user(discord_user_id)

                print(f"discord id: {discord_user_id}")
                print(f"user object: {user}")

                em.description += f"\n{puzzle_ranking:04d} - {user.display_name}"

            except Exception as e:
                # [TODO] delete the user record if not found
                print(f"unhandled exception: {repr(e)}")
            
            
        return await interaction.response.send_message(embed=em)

