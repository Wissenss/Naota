import discord
from discord.ext import commands

import logging

from settings import *

import connectionPool
from utils import permissionsUtils

class CustomCog(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
    
    async def cog_before_invoke(self, ctx: commands.Context):
        LOGGER.log(logging.INFO, f"{ctx.command.name} called (USER ID {ctx.author.id}) (GUILD ID: {ctx.guild.id})")

        self.ensure_user_record(ctx.author.id)

    async def cog_before_slash_invoke(self, interaction: discord.Interaction):
        LOGGER.log(logging.INFO, f"{interaction.command.name} called (USER ID {interaction.user.id}) (GUILD ID: {interaction.guild.id})")

        self.ensure_user_record(interaction.user.id)

    async def cog_check(self, ctx: commands.Context) -> bool:
        cog_allowed = permissionsUtils.cog_allowed_in_context(ctx, self)
    
        if not cog_allowed:
            await self.on_cog_permission_denied(ctx)

        return cog_allowed

    async def on_command_permission_denied(self, ctx : commands.Context):
        em = discord.Embed(title="", description="", color=discord.Color.red())
        
        em.description = f"permission denied for command **{ctx.command.name}**"

        LOGGER.log(logging.ERROR, em.description)

        return await ctx.send(embed=em) 
    
    async def on_cog_permission_denied(self, ctx : commands.Context):
        em = discord.Embed(title="", description="", color=discord.Color.red())
        
        em.description = f"permission denied for cog **{self.__cog_name__}**"

        LOGGER.log(logging.ERROR, em.description)

        return await ctx.send(embed=em)
    
    async def log_and_show_exception(self, interaction : discord.Interaction, e : Exception):
        em = discord.Embed(title="", description=f"exception on {interaction.command.name}: {repr(e)}")
        
        LOGGER.log(logging.ERROR, em.description)

        return await interaction.response.send_message(embed=em)
    
    def ensure_user_record(self, discord_user_id : int):
        print("ensuring user record...")
        conn = connectionPool.get_connection()
        curs = conn.cursor()

        curs.execute("SELECT * FROM users WHERE discord_user_id = ?;", [discord_user_id])

        if not curs.fetchone():
            print(f"the record does not exists... user_id: {discord_user_id}")

            params = [
                discord_user_id,
                0
            ]

            curs.execute("INSERT INTO users(discord_user_id, puzzles_ranking) VALUES(?, ?)", params)
            
            conn.commit()

        connectionPool.release_connection(conn)
