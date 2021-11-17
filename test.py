import pyautogui as ag
import pygetwindow as gw
import os, winshell, win32com.client, pythoncom, sys
from subprocess import Popen, CREATE_NEW_CONSOLE
from tkinter import Tk

#clean env
def clean():
  window_list = gw.getAllWindows()
  for window in window_list:
    window.minimize()

#try to launch game, if not already launched. If err, log err
def normalize(game_server):
  try:
    game_server = gw.getWindowsWithTitle(game_server)[0]
  except:
    launch = input("Game server not running. Would you like to launch? Enter 'y' or 'n' ")
    if launch == "y":
      print("this prints")
      os.startfile("minecraft.bat", 'open')
      print("so does this")
target = os.path.abspath("C:/MinecraftServer/eula.txt")
game_server = gw.getWindowsWithTitle("Minecraft server")[0]
game_server.activate()
ag.moveTo((game_server.left + (game_server.width / 2)), (game_server.top + (game_server.height - 20)))
ag.click()
ag.typewrite("/list\n")

ag.move(0, -45)
ag.tripleClick()
ag.hotkey("ctrl", "c")

clipboard = Tk()
clipboard.withdraw()
val = clipboard.clipboard_get()
num_players = val.split(" ")[4]
print(val)
print(num_players)