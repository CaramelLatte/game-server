from flask import Blueprint, send_file, jsonify
import datetime
import logging
import json
from manager import server_manager

# Create a blueprint for game-related routes
game_bp=Blueprint("game_bp", __name__)

@game_bp.route('/update')
def serv_stats():
    #Return the current server status.
    try:
        server_list = []
        for game in server_manager.game_list:
            server_list.append({
                "name": game.name,
                "icon": game.icon,
                "status": game.running,
                "port": game.ports[0]
            })
        return json.dumps({
            "active_server": server_manager.active_server,
            "player_count": len(server_manager.connected_players),
            "players": server_manager.connected_players,
            "games": server_list
        })
    except Exception as e:
        logging.error(f"Error in /update endpoint: {e}")
        return jsonify({"error": "Failed to fetch server stats"}), 500

@game_bp.route('/image/<gameid>')
def return_image(gameid: str):
    #Return the image for a specific game.
    try:
        for game in server_manager.game_list:
            if game.name.lower() == gameid.lower():
                image_path = f"static/{game.icon}.png"
                return send_file(image_path, mimetype='image/png')
        return "No image found", 404
    except Exception as e:
        logging.error(f"Error in /image/{gameid} endpoint: {e}")
        return jsonify({"error": "Failed to fetch image"}), 500

@game_bp.route('/<gameid>/<cmd>')
def exec_cmd_on_game(gameid: str, cmd: str):
    #Execute a command on a specific game server. Right now only start and stop are supported. Additional commands may be added in server.py later.
    try:
        for game in server_manager.game_list:
            if game.name.lower() == gameid.lower():
                result = game.exec_cmd(cmd)
                if cmd == "start":
                    if server_manager.active_server and server_manager.active_server != game.name:
                        logging.warning(f"Attempted to start {game.name} while {server_manager.active_server} is already running.")
                        return jsonify({"error": "Another server is already running"}), 400
                    if "started" in result:
                        server_manager.active_server = game.name
                        server_manager.empty_time = datetime.datetime.now()
                        logging.info(f"{game.name} server started.")
                elif cmd == "stop":
                    if "stopped" in result:
                        server_manager.active_server = ""
                        server_manager.connected_players = []
                        logging.info(f"{game.name} server stopped.")
                return jsonify({
                    "active_server": server_manager.active_server,
                    "player_count": len(server_manager.connected_players),
                    "players": server_manager.connected_players,
                    "result": result
                })
        logging.error(f"Game {gameid} not found.")
        return jsonify({"error": "Game not found"}), 404
    except Exception as e:
        logging.error(f"Error in /{gameid}/{cmd} endpoint: {e}")
        return jsonify({"error": "Failed to execute command"}), 500