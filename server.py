from flask import Flask, send_file
from flask_cors import CORS
from games import *
import datetime
import json
import dotenv
from threading import Timer

app = Flask(__name__)
CORS(app)
dotenv.load_dotenv()
active_server = ""
connected_players = []
max_empty_time = 20  # value in minutes to allow server to be empty before stopping it. 0 means server will never stop due to inactivity.
empty_time = datetime.datetime.now()

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


def update():
    global active_server
    global connected_players
    global empty_time
    global max_empty_time

    active_server = ""
    connected_players = []

    for game in game_list:
        game.check_if_running()
        if game.running:
            active_server = game.name
            players = game.get_connected_players()
            if len(players) > 0:
                # Update player list and reset empty time if players are found
                empty_time = datetime.datetime.now()
                connected_players.extend(players)
            else:
                # empty_time = datetime.datetime.now()
                continue

    print(f"Connected players: {connected_players}, {len(connected_players)}")
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

rt = RepeatedTimer(2, update) # Periodic update every 2 minutes

@app.route('/update')
def serv_stats():
    server_list = []
    update()
    for game in game_list:
        game.check_if_running()
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

            # Check for idle timeout after command execution
            if len(connected_players) == 0 and (datetime.datetime.now() - empty_time).total_seconds() / 60 >= max_empty_time:
                if game.running:
                    game.exec_cmd("stop")
                    active_server = ""
            return json.dumps({
                "active_server": active_server,
                "player_count": len(connected_players),
                "players": connected_players,
                "result": result
            })
    return json.dumps({"error": "Game not found"})

if __name__ == "__main__":
    chain = os.getenv("SSL_CHAIN")
    privkey = os.getenv("SSL_PRIVKEY")
    app.run(ssl_context=(chain, privkey), host="0.0.0.0", port=8080)

rt.stop()  # Stop the timer when the script ends