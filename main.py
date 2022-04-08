from flask import Flask
from threading import Timer
from time import sleep
from serv import *
import pywinctl as wc
import pyautogui as ag

app = Flask(__name__)
active_server = ""
player_count = 0

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
  global active_server
  active_server = ""
  for game in game_list:
    try:
      is_active = wc.getWindowsWithTitle(game.name)[0]
    except:
      pass
    else:
      active_server = game.name
      file = open(game.log_file, 'r')
      for line in file:
        connected_players = []
        online = 0
        if line.__contains__('connected'):
          #code to parse username here
          online += 1
        elif line.__contains__('disconnected'):
          #code to parse username here
          online -= 1
        player_count = online
      print(f"Active sever is {active_server}")
      print(f'Online players: {player_count}')




rt = RepeatedTimer(3, update_status)
try:
  sleep(1)
  @app.route('/')
  def home():
    return "No. Go away."
  @app.route('/minecraft')
  def mine_stats():
    return 0
  @app.route('/minecraft/start')
  def start_mine():
    minecraft_serv.launch()
    return("Starting..")
  @app.route('/minecraft/stop')
  def stop_mine():
    return 0
  @app.route('/valheim')
  def val_stats():
    return 0
  @app.route('/valheim/start')
  def start_val():
    val_serv.launch()
    sleep(30)
    return("Starting..")
  @app.route('/valheim/stop')
  def stop_val():
    return 0



  if __name__ == "__main__":
    try:
      app.run(ssl_context=('/etc/letsencrypt/archive/games.caramellatte.dev/fullchain1.pem', '/etc/letsencrypt/archive/games.caramellatte.dev/privkey1.pem'), host="0.0.0.0", port=8080)
    except:
      app.run(host='0.0.0.0', port=3000)


finally:
  rt.stop()