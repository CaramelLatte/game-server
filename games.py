import docker
import os
from utils import get_steam_username
import logging
from typing import List, Dict, Optional, Union

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GameServer:
    def __init__(
        self,
        name: str,
        icon: str,
        ports: List[int],
        image: str,
        container_name: str,
        env_vars: Optional[Dict[str, str]] = None,
        volume: Optional[Union[str, Dict[str, str]]] = None,  # accept string (legacy) or dict {"host": "...", "container": "...">
        log_strings: Optional[Dict[str, str]] = None,
        mods: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name: str = name
        self.icon: str = icon
        self.ports: List[int] = ports
        self.image: str = image
        self.container_name: str = container_name
        self.env_vars: Dict[str, str] = env_vars or {}
        self.volume: Optional[Union[str, Dict[str, str]]] = volume  # host path or {"host": "...", "container": "...">
        self.log_strings: Optional[Dict[str, str]] = log_strings
        self.running: bool = False
        self.client: docker.DockerClient = docker.from_env()

    def get_connected_players(self) -> List[str]:
        try:
            if not self.log_strings:
                return []
            connected_players: List[str] = []
            container = self.client.containers.get(self.container_name)
            logs = container.logs(stream=False)
            if logs:
                log_lines = logs.decode('utf-8').split('\n')
                
                # Log files are persistent across container restarts, so we use a string generated early in the server's lifetime to determine if the server has been restarted, so that we can clear old player names from the list.
                for line in log_lines:
                    if self.log_strings["new_instance"] in line:
                        logging.info(f"New server instance detected for {self.name}. Clearing old player names.")
                        for player in connected_players:
                            connected_players.remove(player)

                    # Check for player connection and disconnection events.
                    if len(self.log_strings["connect_tail"]) == 0:
                        if self.log_strings["connect_head"] in line:
                            start = line.index(self.log_strings["connect_head"]) + len(self.log_strings["connect_head"])
                            player_name = line[start:].strip()
                            connected_players.append(player_name)
                            logging.info(f"Player connected: {player_name}")
                    elif self.log_strings["connect_head"] in line and self.log_strings["connect_tail"] in line:
                        start = line.index(self.log_strings["connect_head"]) + len(self.log_strings["connect_head"])
                        end = line.index(self.log_strings["connect_tail"])
                        player_name = line[start:end].strip()
                        connected_players.append(player_name)
                        logging.info(f"Player connected: {player_name}")

                    if len(self.log_strings["disconnect_tail"]) == 0:
                        if self.log_strings["disconnect_head"] in line:
                            start = line.index(self.log_strings["disconnect_head"]) + len(self.log_strings["disconnect_head"])
                            player_name = line[start:].strip()
                            if player_name in connected_players:
                                connected_players.remove(player_name)
                                logging.info(f"Player disconnected: {player_name}")
                    elif self.log_strings["disconnect_head"] in line and self.log_strings["disconnect_tail"] in line:
                        start = line.index(self.log_strings["disconnect_head"]) + len(self.log_strings["disconnect_head"])
                        end = line.index(self.log_strings["disconnect_tail"])
                        player_name = line[start:end].strip()
                        if player_name in connected_players:
                            connected_players.remove(player_name)
                            logging.info(f"Player disconnected: {player_name}")

            # Check for Steam IDs in the connected players list, and replace them with the corresponding Steam usernames using the Steam API.
            for player in connected_players:
                if player.isdigit() and len(player) == 17:  # Check if it's a 17-digit number (likely a Steam ID)
                    steam_username = get_steam_username(player)
                    if steam_username:
                        connected_players[connected_players.index(player)] = steam_username
                        logging.info(f"Replaced Steam ID {player} with username {steam_username}")
                    else:
                        logging.warning(f"Could not resolve Steam ID {player} to a username. Keeping the numeric ID as the player name.")
        except docker.errors.NotFound:
            logging.error(f"Container {self.container_name} not found while fetching connected players.")
        except Exception as e:
            logging.error(f"Error fetching connected players for {self.name}: {e}")
        return connected_players

    def check_if_running(self) -> None:
        try:
            container = self.client.containers.get(self.container_name)
            self.running = container.status == "running"
        except docker.errors.NotFound:
            self.running = False
            logging.warning(f"Container {self.container_name} not found.")
        except Exception as e:
            self.running = False
            logging.error(f"Error checking if {self.name} is running: {e}")

    def exec_cmd(self, command: str) -> str:
        try:
            self.check_if_running()
            if command == "start":
                if not self.running:
                    try:
                        # Check if the container already exists
                        container = self.client.containers.get(self.container_name)
                        # Start the existing container
                        container.start()
                        logging.info(f"{self.name} server started.")
                        return f"{self.name} started"
                    except docker.errors.NotFound:
                        # If the container doesn't exist, check if the image exists and pull it if not
                        images = self.client.images.list(name=self.image)
                        if not images:
                            #pull the image if it doesn't exist
                            pull_result = self.pull_image()
                            logging.info(f"Pulled image for {self.name}: {pull_result}")
                            return f"Pulled image for {self.name}: {pull_result}"

                        # Now safe to run
                        self.client.containers.run(
                            self.image,
                            name=self.container_name,
                            ports={**{f"{port}/tcp": port for port in self.ports}, **{f"{port}/udp": port for port in self.ports}},
                            environment=self.env_vars,
                            volumes=self._build_volumes(),
                            detach=True,
                        )
                        logging.info(f"{self.name} server container created and started.")
                        return f"{self.name} started"
                else:
                    logging.info(f"{self.name} is already running.")
                    return f"{self.name} is already running"
            elif command == "stop":
                if self.running:
                    container = self.client.containers.get(self.container_name)
                    container.stop()
                    logging.info(f"{self.name} server stopped.")
                    return f"{self.name} stopped"
                else:
                    logging.info(f"{self.name} is not running.")
                    return f"{self.name} is not running"
            else:
                logging.warning(f"Unknown command: {command}")
                return f"Unknown command: {command}"
        except docker.errors.APIError as e:
            logging.error(f"Docker API error while executing '{command}' on {self.name}: {e}")
            return f"Error executing '{command}' on {self.name}"
        except Exception as e:
            logging.error(f"Unexpected error while executing '{command}' on {self.name}: {e}")
            return f"Unexpected error: {e}"
        
    def pull_image(self) -> str:
        try:
            self.client.images.pull(self.image)
            logging.info(f"Image {self.image} pulled successfully.")
            return f"Image {self.image} pulled successfully."
        except docker.errors.APIError as e:
            logging.error(f"Docker API error while pulling image {self.image}: {e}")
            return f"Error pulling image {self.image}"
        except Exception as e:
            logging.error(f"Unexpected error while pulling image {self.image}: {e}")
            return f"Unexpected error: {e}"

    def _build_volumes(self) -> Dict[str, Dict[str, str]]:
        """
        Build a docker-py compatible volumes dict.
        Accepts:
          - self.volume as a string -> host path mounted to the same path inside container
          - self.volume as dict -> {"host": "/host/path", "container": "/container/path"}
          - self.mods as dict -> {"host_mod_path": "/host/path", "container_mod_path": "/container/path"}
        Ensures host directories exist (os.makedirs(..., exist_ok=True)) to avoid Docker creating unexpected dirs.
        """
        vols: Dict[str, Dict[str, str]] = {}
        
        host_base = self.volume
        container_base = self._get_image_working_dir()
        host_base_abs = os.path.abspath(host_base)
        os.makedirs(host_base_abs, exist_ok=True)
        vols[host_base_abs] = {"bind": container_base, "mode": "rw"}
        return vols

    def _get_image_working_dir(self) -> str:
        try:
            image = self.client.images.get(self.image)
            image_config = image.attrs['Config']
            work_dir = image_config.get('WorkingDir')
            if work_dir:
                logging.info(f"Found working directory for {self.image}: {work_dir}")
                return work_dir
            else:
                logging.warning(f"No WorkingDir found in {self.image}, using default /data")
                return '/data'
        except docker.errors.ImageNotFound:
            logging.error(f"Image: {self.image} not found, using default /data")
            return '/data'
        except Exception as e:
            logging.error(f"An error occurred: {e}, using default /data")
            return '/data'

# Define the game list and add individual game server objects to it
game_list = []

# Refer to the GameServer class for more information on the parameters required to create a new game server object.
minecraft_serv = GameServer(
    "Minecraft",
    "minecraft",
    [25565],
    "itzg/minecraft-server",
    "minecraft_server",
    {"EULA": "TRUE"},
    "/home/gameserver/minecraft/",
    {
        "connect_head": ": ",
        "connect_tail": "joined the game",
        "disconnect_head": ": ",
        "disconnect_tail": "left the game",
        "new_instance": "Done (",
    },
)
val_serv = GameServer(
    "Valheim",
    "valheim",
    [2456, 2457],
    "mbround18/valheim",
    "valheim-server",
    {"NAME": "Nerds", "WORLD": "Nerdaria", "PUBLIC": 1, "PASSWORD": "onlynerdsplayvalheim", "TYPE": "BepInEx"},
    "/home/gameserver/valheim/",
    {
        "connect_head": "Got handshake from client ",
        "connect_tail": "",
        "disconnect_head": "Closing socket ",
        "disconnect_tail": "",
        "new_instance": "Starting Valheim server",
    }, 
)
seven_days_serv = GameServer(
    "7 Days to Die",
    "7days",
    [26900, 26901, 26902, 26903],
    "didstopia/7dtd-server",
    "7days_server",
    {},
    "/home/gameserver/7-days-to-die/",
    {
        "connect_head": "GMSG: Player '",
        "connect_tail": "' joined the game",
        "disconnect_head": "GMSG: Player '",
        "disconnect_tail": "' left the game",
        "new_instance": "Running as user: docker",
    },
)
pal_server = GameServer(
    "Palworld",
    "palworld",
    [8211],
    "kagurazakanyaa/palworld",
    "palworld_server",
    {},
    "/home/gameserver/palworld/",
    {
        "connect_head": "[LOG] ",
        "connect_tail": " joined the server",
        "disconnect_head": "[LOG] ",
        "disconnect_tail": " left the server",
        "new_instance": "Running Palworld dedicated server",
    },
)

vrising_serv = GameServer(
    "V Rising",
    "vrising",
    [9876, 9877],
    "trueosiris/vrising",
    "vrising_server",
    {},
    "/home/gameserver/v-rising/",
    {
        "connect_head": "BeginAuthSession for SteamID: ",
        "connect_tail": " Result: ",
        "disconnect_head": "EndAuthSession platformId: ",
        "disconnect_tail": "",
        "new_instance": "Launching wine64 V Rising",
    },
)

terraria_serv = GameServer(
    "Terraria",
    "terraria",
    [7777],
    "passivelemon/terraria-docker",
    "terraria_server",
    {},
    "/home/gameserver/terraria/",
    {
        "connect_head": "",
        "connect_tail": " has joined",
        "disconnect_head": "",
        "disconnect_tail": " has left", 
        "new_instance": ": Server Started",
    },
)

game_list.append(minecraft_serv)
game_list.append(val_serv)
game_list.append(seven_days_serv)
game_list.append(pal_server)
game_list.append(vrising_serv)
game_list.append(terraria_serv)
