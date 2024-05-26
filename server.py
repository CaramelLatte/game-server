from flask import Flask
from flask_cors import CORS
from threading import Timer
from time import sleep
from games import *
import datetime
import json

app = Flask(__name__)
CORS(app)
active_server = ""
player_count = 0 
delay = False
delay_time = datetime.datetime.now()
connected_players = [] 
lease_time = 0 #value in minutes to block additional start/stop commands after a new game server instance is begun. 0 means server will allow all start/stop commands always.

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
    active_server = ""
    for game in game_list:
        game.check_if_running()
        if game.running == True:
            break
    if game.running == True:
        active_server = game.name
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
        file.close()
    if active_server == "":
        for player in connected_players:
            connected_players.remove(player)
        delay = False

rt = RepeatedTimer(10, update_status)

@app.route('/')
def home():
    return "No. Go away."
@app.route('/update')
def serv_stats():
    update_status()
    server_list = {}
    for game in game_list:
        server_list.update({game.name : game.icon})
    return json.dumps({"active_server" : active_server, "player_count" : len(connected_players),"players" : connected_players, "returnval" : "0", "game_servers": server_list})

@app.route('/<gameid>')
def gamecheck(gameid):
    gameid = gameid
    for game in game_list:
        if gameid == game.name:
            return str(game.running)

@app.route('/<gameid>/<cmd>')
def exec_cmd_on_game(gameid, cmd):
    gameid = gameid
    cmd = cmd
    global delay_time
    global active_server
    global delay
    for game in game_list:
        if game.name == gameid:
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
            return json.dumps({"active_server" : active_server, "player_count": len(connected_players),"players" : connected_players, "returnval": returnval})
        

if __name__ == "__main__":
    try:
      print("Attempting to start HTTPS server.")
      app.run(ssl_context=('/etc/letsencrypt/archive/games.caramellatte.dev/fullchain1.pem', '/etc/letsencrypt/archive/games.caramellatte.dev/privkey1.pem'), host="0.0.0.0", port=8080)
    except:
        print("Server cannot start, aborting")

rt.stop()