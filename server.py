from flask import Flask, send_file
from flask_cors import CORS
from games import *
import datetime
import json
import dotenv
from threading import Timer
import requests
import subprocess

app = Flask(__name__)
CORS(app)
dotenv.load_dotenv()
active_server = ""
connected_players = []
max_empty_time = 20  # value in minutes to allow server to be empty before stopping it. 0 means server will never stop due to inactivity.
empty_time = datetime.datetime.now()

# Timer class to run the update function periodically
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

def get_server_status():
    # Function to get the status of all servers
    global game_list
    global active_server
    for game in game_list:
        game.check_if_running()
        if game.running:
            active_server = game.name
            break
def get_connected_players():
    # Function to get the list of connected players from the active server
    global active_server
    global connected_players
    connected_players = []  # Reset the list of connected players
    for game in game_list:
        if game.name == active_server:
            players = game.get_connected_players()
            if players and len(players) > 0:
                connected_players.extend(players)
            else:
                connected_players = []

def idle_timeout_check():
    # Function to check if the server is idle for a certain amount of time
    global active_server
    global connected_players
    global empty_time
    global max_empty_time

    if max_empty_time > 0 and len(connected_players) == 0 and active_server != "":
        empty_check = datetime.datetime.now()
        difference = (empty_check.minute + (empty_check.hour * 60)) - (empty_time.minute + (empty_time.hour * 60))
        if difference >= max_empty_time:
            for game in game_list:
                if game.running == True:
                    game.exec_cmd("stop")
                    print(f"Server {game.name} stopped due to inactivity")
                    active_server = ""
            empty_time = datetime.datetime.now()

def perform_health_check():
    try:
        HEALTH_CHECK_URL = os.getenv("HEALTH_CHECK_URL")
        if not HEALTH_CHECK_URL:
            print("HEALTH_CHECK_URL not set in environment variables.")
            return
        request = requests.get(HEALTH_CHECK_URL, timeout=5)
        if request.status_code != 200:
            print("Health check failed!")
            subprocess.run(["systemctl", "restart", "game-server.service"], check=True)
    except requests.exceptions.RequestException as e:
        print(f"Health check request failed: {e}")
        subprocess.run(["systemctl", "restart", "game-server.service"], check=True)

def update():
    get_server_status()
    get_connected_players()
    idle_timeout_check()
    perform_health_check()

rt = RepeatedTimer(10, update) # Periodic update every 10 seconds

@app.route('/update')
def serv_stats():
    update()
    server_list = []
    for game in game_list:
        server_list.append({
            "name": game.name,
            "icon": game.icon,
            "status": game.running,
            "port": game.ports[0]
        })
    return json.dumps({
        "active_server": active_server,
        "player_count": len(connected_players),
        "players": connected_players,
        "games": server_list
    })

@app.route('/image/<gameid>')
def return_image(gameid):
    for game in game_list:
        if game.name.lower() == gameid.lower():
            image_path = f"static/{game.icon}.png"
            return send_file(image_path, mimetype='image/png')
    return "No image found"


#Server commands presently only support start and stop. More commands will be added specific to each game at a later date.
@app.route('/<gameid>/<cmd>')
def exec_cmd_on_game(gameid, cmd):
    global active_server
    global connected_players
    global empty_time
    global max_empty_time
    for game in game_list:
        if game.name.lower() == gameid.lower():
            result = game.exec_cmd(cmd)
            if cmd == "start":
                # Only allow start if no other server is running
                if active_server and active_server != game.name:
                    return json.dumps({"error": "Another server is already running"})
                if "started" in result:
                    active_server = game.name
                    empty_time = datetime.datetime.now()  # Reset empty time on server start
            elif cmd == "stop":
                if "stopped" in result:
                    active_server = ""
                    connected_players = []  # Clear player list when server stops

            return json.dumps({
                "active_server": active_server,
                "player_count": len(connected_players),
                "players": connected_players,
                "result": result
            })
    return json.dumps({"error": "Game not found"})

@app.route('/health')
def health_check():
    return json.dumps({"status": "ok"}), 200

if __name__ == "__main__":
    chain = os.getenv("SSL_CHAIN")
    privkey = os.getenv("SSL_PRIVKEY")
    app.run(ssl_context=(chain, privkey), host="0.0.0.0", port=8080)

rt.stop()  # Stop the timer when the script ends. Server behaves weirdly if you don't do this.