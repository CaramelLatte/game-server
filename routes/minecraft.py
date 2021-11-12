import os
import pyautogui as ag
import pygetwindow as gw
routes = {
  "/" : "Play Minecraft",
  "/goodbye" : "Stop playing minecraft"
}

def closeGame():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
    game_server.close()
  except:
    return "<p>Game not running</p>"
  else:
    return "<p>Game server closed!</p>"

def normalize():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
  except:
    launch = "y"
    if launch == "y":
      os.startfile("minecraft.bat", 'open')

def check():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
  except:
    return "<p>Game is not running!</p>"
  else:
    return "<p>Game is online!</p>"