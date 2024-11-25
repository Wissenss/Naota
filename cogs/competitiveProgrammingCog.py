import codeforces_api.types
import discord
from discord.ext import tasks, commands

import os
import asyncio
import random
import codeforces_api
import selenium
import selenium.webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from cogs.customCog import CustomCog
from settings import *


class CompetitiveProgramming(CustomCog):
  """The competitive programming command interface"""
  def __init__(self, bot : commands.Bot):
    super().__init__(bot)

    self.__cog_name__ = "CompetitiveProgramming"
    #self.cf_api = codeforces_api.CodeforcesApi(CODEFORCES_TOKEN, )
    self.cf_api = codeforces_api.CodeforcesApi()

    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    self.web_driver = selenium.webdriver.Chrome(options)

  def scrap_problem_statement(self, problem_url):
    LOGGER.log(logging.DEBUG, f"starting scrap_problem_statement... (problem_url: {problem_url})")

    self.web_driver.get(problem_url)

    raw_statement = self.web_driver.find_element(by=By.CLASS_NAME, value="problem-statement")

    # LOGGER.log(logging.DEBUG, "raw_statement content: ")

    # for i, child in enumerate(raw_statement.find_elements(By.TAG_NAME, "div")):
    #   LOGGER.log(logging.DEBUG, f"{i}. {child.text}")

    statement = ""

    # last time checked the problem statement <div> had the following content:
    # 
    # <div class="header"></div> // no useful info here
    # <div>
    #   <center></center>
    #   <p></p> // various <p> elements with the problem statement
    # </div>  

    # get the formulation 1/4
    LOGGER.log(logging.DEBUG, "obtaining problem formulation (1/4)...")
    formulation = ""

    formulation_div = raw_statement.find_elements(By.TAG_NAME, "div")[10]

    #LOGGER.log(logging.DEBUG, f"  formulation_div: {formulation_div.text}")

    formulation_list = formulation_div.find_elements(by=By.TAG_NAME, value="p")

    #LOGGER.log(logging.DEBUG, f"  formulation_list: {formulation_list}")

    for item in formulation_list:
      for i, element in enumerate(item.find_elements(By.CSS_SELECTOR, "*")):
        print(f"{i}: {element.tag_name} {element.text[:50]}")

    statement += formulation

    # get the input specification 2/4

    # get the output specification 3/4

    # get the simple tests 4/4

    LOGGER.log(logging.DEBUG, f"final statement: \n {statement}")

    return statement
 
  @commands.hybrid_command(brief="break out the algorithms", description="get a codeforces problem")
  async def problem(self, ctx : commands.Context):
    response : codeforces_api.types.Problem = self.cf_api.problemset_problems()

    #print(response)
    problem = response["problems"][0]
    statistics = response["problem_statistics"][0]

    #print(problem.to_dict())
    #print(statistics.to_dict())

    problem_url = f"https://codeforces.com/problemset/problem/{problem.contest_id}/{problem.index}"

    statement = self.scrap_problem_statement(problem_url)
