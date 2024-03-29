from flask import Flask
from flask_cors import CORS
from threading import Timer
from time import sleep
from serv import *
import pywinctl as wc
import pyautogui as ag
import datetime
import json

app = Flask(__name__)
CORS(app)
active_server = ""
player_count = 0
delay = False
hosting = False
delay_time = datetime.datetime.now()
player_count = 0
connected_players = []

def checktime():
  global delay
  global delay_time
  check_time = datetime.datetime.now()
  difference = check_time.minute + (check_time.hour * 60) - (delay_time.minute + (delay_time.hour * 60))
  if difference >= 10:
    delay = False
  else:
    return


class RepeatedTimer(object):
  def __init__(self, interval, function):
    self._timer = None
    self.interval = interval
    self.function = function
    self.is_running = False
    self.start()
  def _run(self):
    self.is_running = False
    self.start()
    self.function()

  def start(self):
      if not self.is_running:
          self._timer = Timer(self.interval, self._run)
          self._timer.start()
          self.is_running = True

  def stop(self):
      self._timer.cancel()
      self.is_running = False

def clean_windows():
  for game in game_list:
    try:
      open_windows = wc.getWindowsWithTitle(game.name)
    except:
      continue
    else:
      while len(open_windows) >= 1:
        open_windows[-1].close()
        #open_windows.pop(-1)
  return
        
def update_status():
  checktime()

  global connected_players
  global active_server
  global player_count
  active_server = ""
  for game in game_list:
    try:
      server = wc.getWindowsWithTitle(game.name)[0]
    except:
      pass
    else:
      active_server = game.name
          
    if active_server == game.name:
      file = open(game.log_file["file"], 'r')

      for line in file:
        
        if game.log_file["connect"] in line:
          parsed_name = line[game.log_file["splice_start"]:].strip("\n").replace(game.log_file["connect"], "").replace(" ", "")
          if not parsed_name in connected_players:
            connected_players.append(parsed_name)
            
        elif game.log_file["disconnect"] in line:

          parsed_name = line[game.log_file["splice_start"]:].strip("\n").replace(game.log_file["disconnect"], "").replace(" ", "")
          # print(f"'{parsed_name}'")
          # print(connected_players)
          if(parsed_name in connected_players):
            connected_players.remove(parsed_name)
      file.close()
  if active_server != "":
    print(f'{datetime.datetime.now()}: Active sever is {active_server}\nOnline players: {len(connected_players)}: {connected_players}')
  else:
    print(f"{datetime.datetime.now()}: No active server.")
    player_count = 0


rt = RepeatedTimer(10, update_status)
try:
  sleep(1)
  @app.route('/')
  def home():
    return "No. Go away."
  @app.route('/update')
  def serv_stats():
    return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": "0"})
  @app.route('/minecraft')
  def mine_stats():
    return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": "0"})
  @app.route('/minecraft/start')
  def start_mine():
    global delay
    global delay_time
    global active_server
    if not delay:
      delay = True
      delay_time = datetime.datetime.now()
      clean_windows()
      active_server = "minecraft"
      returnval = minecraft_serv.launch()
      return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": returnval})
    else:
      return("Server is leased. Please try again in a few minutes.")
  @app.route('/minecraft/stop')
  def stop_mine():
    global active_server
    global delay
    if active_server == "minecraft":
      delay = False
      returnval = minecraft_serv.exec_cmd("stop")
      active_server = ""
      return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": returnval})
    else:
        return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": "minecraft not open"})

  @app.route('/valheim')
  def val_stats():
    return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": "0"})
  @app.route('/valheim/start')
  def start_val():
    global delay
    global delay_time
    global active_server
    clean_windows()
    if not delay:
      delay_time=datetime.datetime.now()
      delay = True
      active_server = "valheim"
      returnval = val_serv.launch()
      return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": returnval})
    else:
      return("Server is leased. Please try again in a few minutes.")
  @app.route('/valheim/stop')
  def stop_val():
    global delay
    global active_server
    if active_server == "valheim":
      delay = False
      returnval = val_serv.exec_cmd("stop")
      active_server = ""
      return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": returnval})
    else:
        return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": "valheim not open"})



  if __name__ == "__main__":
    try:
      print("Attempting to start HTTPS server.")
      app.run(ssl_context=('/etc/letsencrypt/archive/games.caramellatte.dev/fullchain1.pem', '/etc/letsencrypt/archive/games.caramellatte.dev/privkey1.pem'), host="0.0.0.0", port=8080)
    except:
      print("SSL certificates not found. Loading http.")
      app.run(host='0.0.0.0', port=3000)


finally:
  rt.stop()