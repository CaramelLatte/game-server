import os
import pyautogui as ag
import pygetwindow as gw
from tkinter import Tk
import time
routes = {
  "/" : "Play Minecraft",
  "/goodbye" : "Stop playing minecraft"
}

def closeGame():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
    game_server.close()
  except:
    return "server offline"
  else:
    return "closing server"

def launch():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
  except:
    os.startfile("minecraft.bat", 'open')
    return "starting server"
  else:
    return "server online"
    
def check():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
  except:
    return "offline"
  else:
    return "online"

def get_players():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
  except:
    return "0"
  else:
    game_server.resizeTo(1300, 600)
    game_server.minimize()
    game_server.restore()
    game_server.activate()
    ag.moveTo((game_server.left + (game_server.width / 2)), (game_server.top + (game_server.height - 20)))
    ag.click()
    ag.typewrite("/list\n")

    ag.move(0, -45)
    time.sleep(1)
    ag.tripleClick()
    ag.hotkey("ctrl", "c")

    clipboard = Tk()
    clipboard.withdraw()
    val = clipboard.clipboard_get()
    num_players = val.split(" ")[4]
    return num_players