import io
import datetime
import discord
from discord.ext import commands
from settings import *
from utils.variousUtils import getDiscordMainColor
from utils import permissionsUtils, achivementsUtils

from cogs.customCog import CustomCog

from multiprocessing.connection import Client

import connectionPool
import win32ui
import win32gui
import ctypes

from PIL import Image, ImageDraw
import keyboard
import mouse
import pyautogui

class KeyboardCog(CustomCog):
  def __init__(self, bot : commands.Bot):
    super().__init__(bot)

    self.__cog_name__ = "Keyboard"

    self.allow_timeout = datetime.datetime.now()
    self.deny_timeout = datetime.datetime.now()

  async def cog_check(self, ctx: commands.Context):
    if await super().cog_check(ctx) == False:
      return False

    # skip check if is allow or deny keyboard commands
    if ctx.command.name in ["allowkeyboard", "denykeyboard"]:
      return True

    # deny the usage if deny_timeout is valid
    if datetime.datetime.now() < self.deny_timeout:
      delta = (self.deny_timeout - datetime.datetime.now()).seconds
      minutes = delta // 60
      seconds = delta % 60

      em = discord.Embed(description=f"access to **keyboard** commands is deny for the next {minutes}m {seconds}s", color=discord.Color.red())
      
      await ctx.send(embed=em)

      return False

    # allow the usage if allow_timeout is valid
    if datetime.datetime.now() < self.allow_timeout:
      return True

    # get the connection
    conn = connectionPool.get_connection()
    curs = conn.cursor()

    # get the list of achivements
    curs.execute("SELECT * FROM achivements a LEFT JOIN achivements_users au ON a.achivement_id = au.achivement_id AND user_id = (SELECT user_id FROM users WHERE discord_user_id = ?);", [ctx.author.id])
    rows = curs.fetchall()

    # close the connection
    connectionPool.release_connection(conn)

    # check if the user has completed all achivements
    for row in rows:
      a_id = row[0]
      a_name = row[1]
      a_description = row[2]
      au_id = row[3]

      completed = au_id != None

      if completed == False:
        em = discord.Embed(description="Complete all achivements to gain access to the keyboar commands. Types `!achivements` for more.", color=discord.Color.red())
        await ctx.send(embed=em)

        return False
      
    return True

  @commands.hybrid_command(brief="press and release the given key", description="press and release one of the following keys: space, down, up, left, right, [a-z], [0-9], click")
  async def press(self, ctx : commands.Context, key):
    # check if the given key is allowed
    allowed_keys = [
                    "space", "down", "up", "left", "right",
                    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "ñ", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                    "click"
                   ]

    key = key.lower()

    if not key in allowed_keys:
      em = discord.Embed(description=f"\"{key}\" is not an allowed key", color=discord.Color.red())
      return await ctx.send(embed=em) 

    # embed response    
    em = discord.Embed(description=f"pressing {key}", color=getDiscordMainColor())

    await ctx.send(embed=em)

    if key == "click":
      mouse.click("left") # left click
    else:
      keyboard.press_and_release(key) # press the key
    

  @commands.hybrid_command(brief="move the mouse", description="Move the mouse by the given x and y offset (Negative y values move the mouse upwards).")
  async def move(self, ctx : commands.Context, x_movement : int, y_movement : int):

    #time = math.sqrt(pow(x_movement, 2) + pow(y_movement, 2)) * 1 # add 0.1 second for each pixel traveled
    time = 1

    mouse.move(x_movement, y_movement, absolute=False, duration=time)

    em = discord.Embed(description=f"moving mouse by x: {x_movement}, y: {y_movement}", color=getDiscordMainColor())

    await ctx.send(embed=em)

  def get_cursor(self):
    hcursor = win32gui.GetCursorInfo()[1]
    hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
    hbmp = win32ui.CreateBitmap()
    hbmp.CreateCompatibleBitmap(hdc, 36, 36)
    hdc = hdc.CreateCompatibleDC()
    hdc.SelectObject(hbmp)
    hdc.DrawIcon((0,0), hcursor)
    
    bmpinfo = hbmp.GetInfo()
    bmpstr = hbmp.GetBitmapBits(True)
    cursor = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1).convert("RGBA")
    
    win32gui.DestroyIcon(hcursor)    
    win32gui.DeleteObject(hbmp.GetHandle())
    hdc.DeleteDC()

    pixdata = cursor.load()

    width, height = cursor.size
    for y in range(height):
        for x in range(width):

            if pixdata[x, y] == (0, 0, 0, 255):
                pixdata[x, y] = (0, 0, 0, 0)

    hotspot = win32gui.GetIconInfo(hcursor)[1:3]

    return (cursor, hotspot)

  @commands.hybrid_command(brief="show the screen", description="take and show a screen shot of the host system.")
  async def screenshot(self, ctx : commands.Context, show_cursor : bool = True):
    em = discord.Embed(color=getDiscordMainColor())

    shot = pyautogui.screenshot()

    # draw the cursor
    if show_cursor:
      cursor, (hotspotx, hotspoty) = self.get_cursor()

      ratio = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

      pos_win = win32gui.GetCursorPos()
      pos = (round(pos_win[0]*ratio - hotspotx), round(pos_win[1]*ratio - hotspoty))

      shot.paste(cursor, pos, cursor)
 
      # draw = ImageDraw.Draw(shot)
      # x, y = pyautogui.position()
      # draw.ellipse((x-7, y-7, x+7, y+7), fill='red')

    byte_shot = io.BytesIO()

    shot.save(byte_shot, "png")

    byte_shot.seek(0)

    file = discord.File(byte_shot, filename="screenshot.png")

    em.set_image(url="attachment://screenshot.png")

    await ctx.send(file=file, embed=em)

    byte_shot.close()

  @commands.hybrid_command(brief="allow control", description="allow keyboard commands to all users", hiden=True)
  async def allowkeyboard(self, ctx : commands.Context, minutes : int = 120):
    if not permissionsUtils.command_allowed_in_context(ctx, ctx.command):
      return await self.on_command_permission_denied(ctx)

    self.allow_timeout = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

    em = discord.Embed(description=f"access to **keyboard** commands is available for the next {minutes} minutes", color=getDiscordMainColor())

    await ctx.send(embed=em)

  @commands.hybrid_command(brief="deny control", description="deny keyboard commands to all users", hiden=True)
  async def denykeyboard(self, ctx : commands.Context, minutes : int = 120):
    if not permissionsUtils.command_allowed_in_context(ctx, ctx.command):
      return await self.on_cog_permission_denied(ctx)
    
    self.deny_timeout = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

    em = discord.Embed(description=f"access to **keyboard** commands is deny for the next {minutes} minutes", color=getDiscordMainColor())

    await ctx.send(embed=em)