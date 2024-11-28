import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
import git
import time
import datetime
import os
import random
from utils import permissionsUtils, achivementsUtils
import tweepy

from cogs.customCog import CustomCog

from cogs.musicPlayerCog import AudioBuffer

class TwitterCog(CustomCog):
  def __init__(self, bot : commands.Bot):
    super().__init__(bot)

    self.__cog_name__ = "Twitter"

    self.twitter_api = tweepy.Client(
      consumer_key=TWITTER_KEY,
      consumer_secret=TWITTER_SECRET,
      bearer_token=TWITTER_BEARER,
      access_token=TWITTER_ACCESS_TOKEN,
      access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
    )

    self.twitter_cache = []
    self.last_time_cached = datetime.datetime.now() - datetime.timedelta(days=2)

  @commands.hybrid_command(brief="the most recent tweets", description="get one of the top 5 most recent tweets from Claudia Sheinbaum Pardo")
  async def sheinbaum(self, ctx : commands.Context):
    em = discord.Embed(title="", description="", color=getDiscordMainColor())

    sheinbaum_twitter_id = 591361197

    if self.last_time_cached < datetime.datetime.now() - datetime.timedelta(days=1):
    # try to update the cache 
      try:
        LOGGER.log(logging.DEBUG, "obtaining tweets from X API")

        response = self.twitter_api.get_users_tweets(id=sheinbaum_twitter_id, max_results=5)
        self.twitter_cache = response.data

        LOGGER.log(logging.DEBUG, f"response: {response.data}")

        self.last_time_cached = datetime.datetime.now()
      except Exception as e:
        LOGGER.log(logging.error, f"exception happend when retrieving tweets: {repr(e)}")
    
    if not self.twitter_cache:
      em.color = discord.Color.red()
      em.description = "Could not retrieve tweets. Most likely the quota was exceeded."
      return await ctx.send(embed=em)
    
    LOGGER.log(logging.DEBUG, f"self.twitter_cache: {self.twitter_cache}")

    # get a random tweet from cache
    tweet = random.choices(self.twitter_cache)[0]

    LOGGER.log(logging.DEBUG, f"tweet: {tweet}")
    LOGGER.log(logging.DEBUG, f"tweet.id: {tweet.id}")
    LOGGER.log(logging.DEBUG, f"tweet.text: {tweet.text}")

    profile_url = "https://x.com/Claudiashein"
    tweet_url = f"https://x.com/Claudiashein/status/{tweet.id}"

    em.set_author(name="Claudia Sheinbaum Pardo", url=tweet_url, icon_url="https://pbs.twimg.com/profile_images/1845487232989483008/xJGRmkR0_400x400.jpg")
    em.description = tweet.text

    await ctx.send(embed=em)

    await achivementsUtils.observe_achivement(6, ctx)