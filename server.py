from flask import Flask, send_file
from flask_cors import CORS
from threading import Timer
from games import *
import datetime
import json

app = Flask(__name__)
CORS(app)
active_server = ""
delay = False
delay_time = datetime.datetime.now()
connected_players = [] 
lease_time = 0 #value in minutes to block additional start/stop commands after a new game server instance is begun. 0 means server will allow all start/stop commands always.
empty_time = datetime.datetime.now()
max_empty_time = 0 #value in minutes to allow server to be empty before stopping it. 0 means server will never stop due to inactivity.

#function used to check if server lease time has elapsed
def checktime():
    global delay
    check_time = datetime.datetime.now()
    difference = (check_time.minute + (check_time.hour * 60)) - (delay_time.minute + (delay_time.hour * 60))
    if difference >= lease_time:
        delay = False
    else:
        return
    
#timer object to initiate periodic status update checks
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

#Function to periodically check if a server is running, and if so, to pull from game's most recent log data to determine connected players
def update_status():
    checktime()
    global delay
    global active_server
    global connected_players
    global empty_time
    global max_empty_time
    active_server = ""

    for game in game_list:
        game.check_if_running()
        if game.running == True:
            active_server = game.name
            if game.log_file["file"] is not None:
                file = open(game.log_file["file"], 'r')
                for line in file:
                    if game.log_file["connect"] in line:
                        parsed_name = line[game.log_file["splice_start"]:].strip("\n").replace(game.log_file["connect"], "").replace(" ", "")
                        if not parsed_name in connected_players:
                            connected_players.append(parsed_name)
                    elif game.log_file["disconnect"] in line:
                        parsed_name = line[game.log_file["splice_start"]:].strip("\n").replace(game.log_file["disconnect"], "").replace(" ", "")
                        if parsed_name in connected_players:
                            connected_players.remove(parsed_name)
                if len(connected_players) >= max_empty_time and max_empty_time > 0:
                    empty_time = datetime.datetime.now()
                file.close()
    if active_server == "":
        for player in connected_players:
            connected_players.remove(player)
        delay = False
        
    if max_empty_time > 0 and len(connected_players) == 0 and active_server != "":
        empty_check = datetime.datetime.now()
        difference = (empty_check.minute + (empty_check.hour * 60)) - (empty_time.minute + (empty_time.hour * 60))
        if difference >= max_empty_time:
            for game in game_list:
                if game.running == True:
                    game.exec_cmd("stop")
            empty_time = datetime.datetime.now()

rt = RepeatedTimer(2, update_status)

@app.route('/')
def home():
    return "No. Go away."
@app.route('/update')
def serv_stats():
    server_list = []
    for game in game_list:
        server_list.append({"name" : game.name, "icon": game.icon, "status": game.running, "port": game.ports[0]})
    return json.dumps({"active_server" : active_server, "player_count" : len(connected_players),"players" : connected_players, "returnval" : "0", "games": server_list})
@app.route('/image/<gameid>')
def return_image(gameid):
    for game in game_list:
        if game.name.lower() == gameid.lower():
            image_path = f"static/{game.icon}.png"
            return send_file(image_path, mimetype='image/png')
    return "No image found"
@app.route('/<gameid>')
def gamecheck(gameid):
    for game in game_list:
        if game.name.lower() == gameid.lower():
            return str(game.running)

@app.route('/<gameid>/<cmd>')
def exec_cmd_on_game(gameid, cmd):
    gameid = gameid
    cmd = cmd
    global delay_time
    global active_server
    global delay
    for game in game_list:
        if game.name.lower() == gameid.lower():
            if cmd == "start":
                if not delay and active_server == "":
                    delay = True
                    delay_time = datetime.datetime.now()
                    active_server = game.name
                else:
                    return("Server is leased. Please try again later.")
            elif cmd == "stop":
                if active_server == game.name and delay == False:
                    active_server = ""
                    
                else:
                    return json.dumps("Server not running")
            returnval = game.exec_cmd(cmd)
            return json.dumps({"active_server" : active_server, "player_count": len(connected_players), "players" : connected_players, "returnval": returnval})
        

if __name__ == "__main__":
    try:
      print("Attempting to start HTTPS server.")
      app.run(ssl_context=('/etc/letsencrypt/archive/games.caramellatte.dev/fullchain1.pem', '/etc/letsencrypt/archive/games.caramellatte.dev/privkey1.pem'), host="0.0.0.0", port=8080)
    except:
        print("Server cannot start, aborting")

rt.stop()