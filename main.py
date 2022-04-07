from flask import Flask
from threading import Timer
from time import sleep

appFlask = Flask(__name__)

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
  print("got here")

rt = RepeatedTimer(30, update_status)
try:
  sleep(1)
  @appFlask.route('/')
  def home():
    return "No. Go away."
  @appFlask.route('/minecraft')
  def mine_stats():
    return 0
  @appFlask.route('/minecraft/start')
  def start_mine():
    pass


  if __name__ == "__main__":
    appFlask.run(ssl_context=('/etc/letsencrypt/archive/games.caramellatte.dev/fullchain1.pem', '/etc/letsencrypt/archive/games.caramellatte.dev/privkey1.pem'), host="0.0.0.0", port=8080)

finally:
  rt.stop()
