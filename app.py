from flask import Flask, jsonify
from flask_cors import CORS
from routes.minecraft import check, closeGame, get_players, launch
import pyautogui as ag
import pygetwindow as gw

app = Flask(__name__)
CORS(app)

def normalize():
  get_windows = gw.getAllWindows()
  for window in get_windows:
    window.minimize()


@app.route("/")
def startGame():
  #returnval = normalize()
  print("got here")
  returnval = launch()
  return jsonify(status=returnval)
@app.route("/close")
def close():
  returnval = closeGame()
  return jsonify(status=returnval)
@app.route("/check")
def check_status():
  return jsonify(
    online_status=check(),
    player_count=get_players()
  )



if __name__ == "__main__":
    from waitress import serve
    host = "0.0.0.0"
    port = 8080
    print("Running server on ", host, port)
    serve(app, host=host, port=port)
