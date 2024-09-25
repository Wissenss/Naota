import discord
from discord.ext import commands

from settings import *

from utils import permissionsUtils

class CustomCog(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
    
    async def cog_before_invoke(self, ctx: commands.Context):
        LOGGER.log(logging.INFO, f"{ctx.command.name} called (USER ID {ctx.author.id}) (GUILD ID: {ctx.guild.id})")

    async def cog_check(self, ctx: commands.Context) -> bool:
        cog_allowed = permissionsUtils.cog_allowed_in_context(ctx, self)
    
        if not cog_allowed:
            await self.on_cog_permission_denied(ctx)

        return cog_allowed

    async def on_command_permission_denied(self, ctx : commands.Context):
        em = discord.Embed(title="", description="", color=discord.Color.red())
        
        em.description = f"permission denied for command **{ctx.command.name}**"

        return await ctx.send(embed=em) 
    
    async def on_cog_permission_denied(self, ctx : commands.Context):
        em = discord.Embed(title="", description="", color=discord.Color.red())
        
        em.description = f"permission denied for cog **{self.__cog_name__}**"

        return await ctx.send(embed=em)
    
    async def on_exception(self, ctx : commands.Context, e : Exception):
        return await ctx.send()