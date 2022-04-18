import pyautogui as ag
import pywinctl as wc
import subprocess
import time

class GameServer:
  def __init__(self, name, port, path, log_file, cmds) -> None:
    self.name = name
    self.port = port
    self.path = path
    self.log_file = log_file
    self.cmds = cmds
    self.connected = 0

  def launch(self):
    try:
      server = wc.getWindowsWithTitle(self.name)[-1]
    except:
      subprocess.call(["lxterminal", "-t", self.name])
      print("Server not found. Starting..")
      time.sleep(2)
      server = wc.getWindowsWithTitle(self.name)[-1]
      server.activate()
      time.sleep(1)
      ag.typewrite("cd " + self.path + "\n")
      time.sleep(1)
      return self.exec_cmd("launch")
    else:
      print("Server already open")
      return "Server already open. If it isn't available, try closing and re-opening, then wait a few minutes."

  def exec_cmd(self, command):
    servers = wc.getWindowsWithTitle(self.name)[0]
    servers.activate()
    time.sleep(1)
    hotkeys = ["ctrl", "shift", "alt"]
    for key in hotkeys:
      if key in self.cmds[command]:
        print("here")
        hotkey = self.cmds[command].split(",")
        ag.hotkey(hotkey[0], hotkey[1])
        return command
    ag.typewrite(self.cmds[command] + "\n")
    return command


game_list = []
minecraft_serv = GameServer("minecraft", [25565], "/home/pi/minecraft/", {"file": "/home/pi/minecraft/logs/latest.log",  "connect": "joined the game", "disconnect": "left the game", "splice_start": 33}, {"launch": "java -Xmx5G -Xms5G -jar server.jar nogui \n", "stop": "/stop\n"})
val_serv = GameServer("valheim", [2456, 2457], "/home/pi/valheim_server/", {"file": "/home/pi/valheim_server/valheim_log.txt", "connect": "Got handshake from client", "disconnect": "Closing socket", "splice_start": 20}, {"launch": "./start_server.sh", "stop": "ctrl,c"})
game_list.append(minecraft_serv)
game_list.append(val_serv)