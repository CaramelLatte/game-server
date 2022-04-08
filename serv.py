import pyautogui as ag
import pywinctl as wc
import subprocess
import time

class GameServer:
  def __init__(self, name, path, log_file, cmds) -> None:
    self.name = name
    self.path = path
    self.log_file = log_file
    self.cmds = cmds
    self.connected = 0

  def launch(self):
    try:
      server = wc.getWindowsWithTitle(self.name)[0]
    except:
      subprocess.call(["lxterminal", "-t", self.name])
      print("Server not found. Starting..")
      time.sleep(2)
      server = wc.getWindowsWithTitle(self.name)[0]
      server.activate()
      time.sleep(1)
      ag.typewrite("cd " + self.path + "\n")
      time.sleep(1)
      self.exec_cmd("launch")
    else:
      print("Server already open")

  def exec_cmd(self, command):
    servers = wc.getWindowsWithTitle(self.name)[0]
    servers.activate()
    time.sleep(1)
    ag.typewrite(self.cmds[command] + "\n")

game_list = []
minecraft_serv = GameServer("minecraft", "/home/pi/minecraft/", "/home/pi/minecraft/logs/latest.log", {"launch": "java -Xmx5G -Xms5G -jar server.jar nogui \n"})
val_serv = GameServer("valheim", "/home/pi/valheim_server/", "/home/pi/valheim_server/valheim_log.txt", {"launch": "./start_server.sh"})
game_list.append(minecraft_serv)
game_list.append(val_serv)