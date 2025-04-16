from flask import Flask, send_file
from flask_cors import CORS
from gamesdocker import *
import datetime
import json

app = Flask(__name__)
CORS(app)
active_server = ""
connected_players = []

@app.route('/update')
def serv_stats():
    server_list = []
    for game in game_list:
        game.check_if_running()
        server_list.append({
            "name": game.name,
            "icon": game.icon,
            "status": game.running,
            "ports": game.ports[0]
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
    app.run(ssl_context=('/etc/letsencrypt/archive/games.caramellatte.dev/fullchain6.pem', '/etc/letsencrypt/archive/games.caramellatte.dev/privkey6.pem'), host="0.0.0.0", port=8080)