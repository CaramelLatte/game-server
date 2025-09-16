import datetime
from typing import List
import docker
import logging
import os
import requests
import subprocess
from games import game_list

class ServerManager:
    #Class to manage the state and operations of game servers.
    def __init__(self, game_list) -> None:
        self.active_server: str = ""
        self.connected_players: List[str] = []
        self.max_empty_time: int = 60  # Minutes to allow server to be empty before stopping
        self.empty_time: datetime.datetime = datetime.datetime.now()
        self.game_list = game_list

    def get_server_status(self) -> None:
        try:
            self.active_server = ""
            for game in game_list:
                game.check_if_running()
                if game.running:
                    self.active_server = game.name
                    break
        except Exception as e:
            logging.error(f"Error getting server status: {e}")

    def get_connected_players(self) -> None:
        try:
            self.connected_players = []
            for game in game_list:
                if game.name == self.active_server:
                    players = game.get_connected_players()
                    if players:
                        self.connected_players.extend(players)
        except Exception as e:
            logging.error(f"Error getting connected players: {e}")

    def idle_timeout_check(self) -> None:
        try:
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
        except Exception as e:
            logging.error(f"Error during idle timeout check: {e}")

    def perform_health_check(self) -> None:
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
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to restart game-server.service: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during health check: {e}")

    def update(self) -> None:
        #Perform periodic updates.
        self.get_server_status()
        self.get_connected_players()
        self.idle_timeout_check()
        self.perform_health_check()

server_manager = ServerManager(game_list)