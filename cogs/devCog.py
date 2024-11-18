import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
import git
import time
import datetime
import os
from utils import permissionsUtils

from cogs.customCog import CustomCog

from cogs.musicPlayerCog import AudioBuffer

class DevCog (CustomCog):
    def __init__(self, bot : commands.Bot):
        super().__init__(bot)

        self.start_time = datetime.datetime.now()
        self.bot = bot
        self.__cog_name__ = "Dev"

    @commands.hybrid_command(brief="pong", description="test for correct bot connection")
    async def ping(self, ctx : commands.Context):
        em = discord.Embed(title="pong!", description="", color=getDiscordMainColor())

        em.description += f"\n**latency:** {round(self.bot.latency * 1000)}ms"
        
        # obtain the buffer size
        count, size = AudioBuffer.get_size()
        em.description += f"\n**buffer size:** {count} files, {size} bytes"

        # get the uptime
        up_time = datetime.datetime.now() - self.start_time
        days, seconds = up_time.days, up_time.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        em.description += f"\n**up time:** {days}d {hours}h {minutes}m {seconds}s"

        await ctx.send(embed=em)

    @commands.hybrid_command(hidden=True)
    async def sync(self, ctx : commands.Context):
        if not permissionsUtils.command_allowed_in_context(ctx, ctx.command):
            return await self.on_command_permission_denied(ctx)

        await self.bot.tree.sync()

        em = discord.Embed(description="syncing commands", color=getDiscordMainColor())

        await ctx.send(embed=em)

    @commands.hybrid_command(brief="shows the most recent changes", description="get a list of all the recent improvements, new features and bug fixes done to naota")
    async def changelog(self, ctx : commands.Context):
        # obtain the log from local repo
        if GIT_REPO:
            repo = git.Repo(GIT_REPO)
        else:
            repo = git.Repo(os.getcwd())

        commit_list = list(repo.iter_commits(all=True))

        # number of commits = version number
        version = f"0.0.{len(commit_list)}"
        
        # show the last 5 commits messages
        logs = ""

        for i in range(5):
            commit = commit_list[i]

            date = time.gmtime(commit.committed_date)
            author = commit.author
            message = commit.message

            logs += f"[{date.tm_year}/{date.tm_mon}/{date.tm_mday}] - {message}\n"

        em = discord.Embed(title=f"Naota v_{version}", description=logs, color=getDiscordMainColor())
        await ctx.send(embed=em)
