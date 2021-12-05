import pyautogui as ag
import pygetwindow as gw
import os
import glob
import time

def mine_check_online():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
  except: 
    #os.startfile("minecraft.bat", 'open')
    return "offline"
  else:
    return "online"

def mine_check_players():
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
    time.sleep(1)
    ag.click()
    time.sleep(1)
    ag.typewrite("/list\n")
    game_server.minimize()
    folder_path = r'C:\Users\jared\OneDrive\Desktop\personalsite\game-test\logs'
    file_type = '\*log'
    files = glob.glob(folder_path + file_type)
    latest_file = max(files, key=os.path.getctime)

    content = open(latest_file)
    last_line = content.readlines()[-1]
    if last_line[44] == " ":
      return last_line[43]
    else:
      return last_line[43] + last_line[44]
    
def mine_close_game():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
    game_server.close()
  except:
    return "offline"
  else:
    return "shutting down.."

def mine_launch():
  try:
    game_server = gw.getWindowsWithTitle("Minecraft server")[0]
  except:
    os.startfile("minecraft.bat", 'open')
    return "starting.."
  else:
    return "online"