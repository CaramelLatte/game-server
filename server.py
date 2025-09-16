from flask import Flask
from flask_cors import CORS
from threading import Timer
import dotenv
import logging
from routes import register_blueprints
import json
import os
import datetime
import requests
import subprocess
from typing import List, Optional


# Initialize Flask app
app = Flask(__name__)
CORS(app)
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RepeatedTimer:
    #Timer class to run a function periodically.
    def __init__(self, interval: int, function: callable) -> None:
        self._timer: Optional[Timer] = None
        self.interval: int = interval
        self.function: callable = function
        self.is_running: bool = False
        self.start()

    def _run(self) -> None:
        self.is_running = False
        self.start()
        self.function()

    def start(self) -> None:
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self) -> None:
        if self._timer:
            self._timer.cancel()
        self.is_running = False


class ServerManager:
    #Class to manage the state and operations of game servers.
    def __init__(self) -> None:
        self.active_server: str = ""
        self.connected_players: List[str] = []
        self.max_empty_time: int = 60  # Minutes to allow server to be empty before stopping
        self.empty_time: datetime.datetime = datetime.datetime.now()

    def get_server_status(self) -> None:
        #Check the status of all servers and update the active server.
        global game_list
        self.active_server = ""
        for game in game_list:
            game.check_if_running()
            if game.running:
                self.active_server = game.name
                break

    def get_connected_players(self) -> None:
        #Get the list of connected players from the active server.
        global game_list
        self.connected_players = []
        for game in game_list:
            if game.name == self.active_server:
                players = game.get_connected_players()
                if players:
                    self.connected_players.extend(players)

    def idle_timeout_check(self) -> None:
        #Stop the server if it has been idle for too long.
        if self.max_empty_time > 0 and not self.connected_players and self.active_server:
            empty_check = datetime.datetime.now()
            difference = (empty_check.minute + (empty_check.hour * 60)) - (self.empty_time.minute + (self.empty_time.hour * 60))
            if difference >= self.max_empty_time:
                global game_list
                for game in game_list:
                    if game.running:
                        game.exec_cmd("stop")
                        logging.info(f"Server {game.name} stopped due to inactivity.")
                        self.active_server = ""
                self.empty_time = datetime.datetime.now()

    def perform_health_check(self) -> None:
        #Perform a health check on the server.
        try:
            health_check_url = os.getenv("HEALTH_CHECK_URL")
            if not health_check_url:
                logging.warning("HEALTH_CHECK_URL not set in environment variables.")
                return
            response = requests.get(health_check_url, timeout=5)
            if response.status_code != 200:
                logging.error("Health check failed!")
                subprocess.run(["systemctl", "restart", "game-server.service"], check=True)
        except requests.exceptions.RequestException as e:
            logging.error(f"Health check request failed: {e}")
            subprocess.run(["systemctl", "restart", "game-server.service"], check=True)

    def update(self) -> None:
        #Perform periodic updates.
        self.get_server_status()
        self.get_connected_players()
        self.idle_timeout_check()
        self.perform_health_check()


# Initialize the ServerManager
server_manager = ServerManager()

# Set up the periodic update timer
rt = RepeatedTimer(10, server_manager.update)

# Register blueprints
register_blueprints(app)

@app.route('/health')
def health_check():
    """Return the health status of the server."""
    return json.dumps({"status": "ok"}), 200

if __name__ == "__main__":
    chain = os.getenv("SSL_CHAIN")
    privkey = os.getenv("SSL_PRIVKEY")
    app.run(ssl_context=(chain, privkey), host="0.0.0.0", port=8080)

rt.stop()  # Stop the timer when the script ends. Server behaves weirdly if you don't do this.