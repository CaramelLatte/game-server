from flask import Flask
from flask_cors import CORS
from threading import Timer
from time import sleep
from serv import *
import pywinctl as wc
import pyautogui as ag
import socket
import datetime
import json

app = Flask(__name__)
CORS(app)
active_server = ""
player_count = 0
delay = False
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
    #delay = True
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

def update_status():
  checktime()
  
  global connected_players
  global active_server
  global player_count
  active_server = ""
  for game in game_list:
      try:
        is_active = wc.getWindowsWithTitle(game.name)[0]
      except:
        continue
      else:
        
        if not delay:
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          try:
            s.bind(("127.0.0.1", int(game.port)))
          except:
            print("Port unavailable")
          else:
            print("port not in use, but game open. closing..")
            is_active.activate()
            sleep(1)
            ag.hotkey("alt", "f4")
          s.close()
          active_server = ""
        active_server = game.name
      
      if active_server == game.name:
        file = open(game.log_file["file"], 'r')

        for line in file:
          
          if game.log_file["connect"] in line:
            parsed_name = line[game.log_file["splice_start"]:].strip("\n").replace(game.log_file["connect"], "").replace(" ", "")
            if not parsed_name in connected_players:
              connected_players.append(parsed_name)
              
          elif game.log_file["disconnect"] in line:
            parsed_name = line[game.log_file["splice_start"]:]
            print(parsed_name.strip("\n").replace(game.log_file["disconnect"], "").replace(" ", ""))
            connected_players.remove(parsed_name.strip("\n").replace(game.log_file["disconnect"], "").replace(" ", ""))
        file.close()
  if active_server != "":
    print(f'{datetime.datetime.now()}: Active sever is {active_server}\nOnline players: {len(connected_players)}: {connected_players}')
  else:
    print(f"{datetime.datetime.now()}: No active server.")
    player_count = 0


rt = RepeatedTimer(60, update_status)
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
    if not delay:
      delay = True
      delay_time = datetime.datetime.now()
      returnval = minecraft_serv.launch()
      return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": returnval})
    else:
      return("Server is leased. Please try again in a few minutes.")
  @app.route('/minecraft/stop')
  def stop_mine():
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
    if not delay:
      delay_time=datetime.datetime.now()
      delay = True
      returnval = val_serv.launch()
      return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "returnval": returnval})
    else:
      return("Server is leased. Please try again in a few minutes.")
  @app.route('/valheim/stop')
  def stop_val():
    global delay
    if active_server == "valheim":
      delay = False
      returnval = minecraft_serv.exec_cmd("stop")
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