from flask import Flask, jsonify
from flask_cors import CORS

import pyautogui as ag
import pygetwindow as gw
import sched, time
from threading import Timer
from time import sleep
from routes.minecraft import mine_check_online, mine_check_players, mine_close_game, mine_launch
from routes.sdtd import sdtd_check_online, sdtd_check_players

app = Flask(__name__)
CORS(app)


class GameServer():
  def __init__(self) -> None:
      self.online_status = "offline"
      self.player_count = 0


mine_serv = GameServer()
sdtd_serv = GameServer()

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
  print("Running check..")
  mine_serv.online_status = mine_check_online()
  if mine_serv.online_status == "online":
    mine_serv.player_count = mine_check_players()
  else:
    mine_serv.player_count = 0

  sdtd_serv.online_status = sdtd_check_online()
  if sdtd_serv.online_status == "online":
    sdtd_serv.player_count = sdtd_check_players()
  else:
    sdtd_serv.player_count = 0

rt = RepeatedTimer(30, update_status)
try:
    sleep(1)

    @app.route("/minecraft")
    def minestate():
      return jsonify(
        online_status = mine_serv.online_status,
        player_count = mine_serv.player_count
        )
    @app.route("/minecraft/start")
    def minestart():
      return jsonify(
        oneline_status = mine_launch(),
        player_count = mine_serv.player_count
      )
    @app.route("/minecraft/stop")
    def minestop():
      return jsonify(
        online_status = mine_close_game(),
        player_count = 0
      )
    if __name__ == "__main__":
      from waitress import serve
      host = "0.0.0.0"
      port = 8080
      print(f"Running server on {host}:{port}")
      serve(app, host=host, port=port)
finally:
    rt.stop()