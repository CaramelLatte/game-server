from urllib.parse import _DefragResultBase
from xmlrpc.client import DateTime
from flask import Flask
from flask_cors import CORS
from threading import Timer
from time import sleep
from serv import *
import pywinctl as wc
import pyautogui as ag
import socket, errno
import datetime
import json

app = Flask(__name__)
CORS(app)
active_server = ""
player_count = 0
delay = False
delay_time = datetime.datetime.now()
print(delay_time)
player_count = 0

def checktime():
  global delay
  check_time = datetime.datetime.now()
  difference = check_time.minute + (check_time.hour * 60) - (delay_time.minute + (delay_time.hour * 60))
  if difference >= 10:
    delay = False
  else:
    delay = True



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
  
  global active_server
  global player_count
  active_server = ""
  for game in game_list:
      try:
        is_active = wc.getWindowsWithTitle(game.name)[0]
      except:
        pass
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
        active_server = game.name
      file = open(game.log_file, 'r')
      for line in file:
        connected_players = []
        online = 0
        if 'connected' in line:
          #code to parse username here
          online += 1
        elif line.__contains__('disconnected'):
          #code to parse username here
          online -= 1
        player_count = online
  if active_server != "":
    print(f"Active sever is {active_server}")
    print(f'Online players: {player_count}')
  else:
    print("No active server.")




rt = RepeatedTimer(30, update_status)
try:
  sleep(1)
  @app.route('/')
  def home():
    return "No. Go away."
  @app.route('/minecraft')
  def mine_stats():
    return json.dumps({"active_server" : active_server, "player_count": player_count, "returnval": "0"})
  @app.route('/minecraft/start')
  def start_mine():
    returnval = minecraft_serv.launch()
    return json.dumps({"active_server" : active_server, "player_count": player_count, "returnval": returnval})

  @app.route('/minecraft/stop')
  def stop_mine():
    returnval = minecraft_serv.exec_cmd("stop")
    return json.dumps({"active_server" : active_server, "player_count": player_count, "returnval": returnval})
  @app.route('/valheim')
  def val_stats():
    return json.dumps({"active_server" : active_server, "player_count": player_count, "returnval": "0"})
  @app.route('/valheim/start')
  def start_val():
    returnval = val_serv.launch()
    return json.dumps({"active_server" : active_server, "player_count": player_count, "returnval": returnval})
  @app.route('/valheim/stop')
  def stop_val():
    returnval = val_serv.exec_cmd("stop")
    return json.dumps({"active_server" : active_server, "player_count": player_count, "returnval": returnval})



  if __name__ == "__main__":
    try:
      print("Attempting to start HTTPS server.")
      app.run(ssl_context=('/etc/letsencrypt/archive/games.caramellatte.dev/fullchain1.pem', '/etc/letsencrypt/archive/games.caramellatte.dev/privkey1.pem'), host="0.0.0.0", port=8080)
    except:
      print("SSL certificates not found. Loading http.")
      app.run(host='0.0.0.0', port=3000)


finally:
  rt.stop()