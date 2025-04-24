from flask import Flask, send_file
from flask_cors import CORS
from games import *
import datetime
import json
import dotenv

app = Flask(__name__)
CORS(app)
dotenv.load_dotenv()
active_server = ""
connected_players = []
max_empty_time = 20  # value in minutes to allow server to be empty before stopping it. 0 means server will never stop due to inactivity.

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
            if players:
                connected_players.extend(players)
            else:
                empty_time = datetime.datetime.now()

    if active_server == "" and (datetime.datetime.now() - empty_time).total_seconds() / 60 >= max_empty_time:
        for game in game_list:
            if game.running:
                game.exec_cmd("stop")
                break
        empty_time = datetime.datetime.now()

@app.route('/update')
def serv_stats():
    server_list = []
    update()
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
            if cmd == "start" and "started" in result:
                active_server = game.name
            elif cmd == "stop" and "stopped" in result:
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