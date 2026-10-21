import docker
from docker.utils import parse_repository_tag
import os
import threading
from utils import get_steam_username
import logging
from typing import List, Dict, Optional, Union

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# States reported to the site. While a start/stop is in one of the busy states, the worker thread owns the state.
BUSY_STATES = {"pulling", "starting", "stopping"}

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
        self.state: str = "stopped"  # stopped | pulling | starting | running | stopping | error
        self.detail: str = ""  # short human-readable note for the current state
        self.progress: Optional[int] = None  # percent, only while pulling
        self._lock = threading.Lock()
        self.client: docker.DockerClient = docker.from_env()

    def set_state(self, state: str, detail: str = "", progress: Optional[int] = None) -> None:
        with self._lock:
            self.state, self.detail, self.progress = state, detail, progress

    def request(self, command: str) -> bool:
        # Run start/stop in the background so a long image pull doesn't hold the HTTP request open (nginx gives up after 60s).
        # Returns False if another action on this game is still in progress.
        with self._lock:
            if self.state in BUSY_STATES:
                return False
            self.state = "starting" if command == "start" else "stopping"
            self.detail, self.progress = "", None
        threading.Thread(target=self._run_cmd, args=(command,), daemon=True).start()
        return True

    def _run_cmd(self, command: str) -> None:
        self.exec_cmd(command)
        # exec_cmd leaves the state alone when there was nothing to do (already running/stopped), so settle it here.
        with self._lock:
            if self.state in BUSY_STATES:
                self.state, self.detail, self.progress = ("running" if self.running else "stopped"), "", None

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
        with self._lock:
            try:
                container = self.client.containers.get(self.container_name)
                self.running = container.status == "running"
                exit_code = container.attrs.get("State", {}).get("ExitCode", 0)
                # A server we last saw running that exits non-zero on its own crashed (docker stop gives 0, 137 or 143).
                if self.state == "running" and container.status == "exited" and exit_code not in (0, 137, 143):
                    logging.error(f"{self.name} server exited unexpectedly with code {exit_code}.")
                    self.state, self.detail, self.progress = "error", f"Server crashed (exit code {exit_code})", None
            except docker.errors.NotFound:
                self.running = False
                logging.warning(f"Container {self.container_name} not found.")
            except Exception as e:
                self.running = False
                logging.error(f"Error checking if {self.name} is running: {e}")
            # Leave busy states to the worker, and keep an error visible until the server comes up or someone tries again.
            if self.state not in BUSY_STATES and not (self.state == "error" and not self.running):
                self.state, self.detail, self.progress = ("running" if self.running else "stopped"), "", None

    def exec_cmd(self, command: str) -> str:
        try:
            self.check_if_running()
            if command == "start":
                if not self.running:
                    try:
                        # Check if the container already exists
                        container = self.client.containers.get(self.container_name)
                        # Start the existing container
                        self.set_state("starting", "Starting container")
                        container.start()
                        self.running = True
                        self.set_state("running")
                        logging.info(f"{self.name} server started.")
                        return f"{self.name} started"
                    except docker.errors.NotFound:
                        # If the container doesn't exist, check if the image exists and pull it if not
                        images = self.client.images.list(name=self.image)
                        if not images:
                            #pull the image if it doesn't exist, then fall through and create the container in the same request
                            self.set_state("pulling", "Downloading Docker image", 0)
                            pull_result = self.pull_image()
                            logging.info(f"Pulled image for {self.name}: {pull_result}")
                            if not self.client.images.list(name=self.image):
                                self.set_state("error", "Docker image download failed")
                                return f"Failed to pull image for {self.name}: {pull_result}"

                        self.set_state("starting", "Creating container")

                        # Now safe to run
                        self.client.containers.run(
                            self.image,
                            name=self.container_name,
                            ports={**{f"{port}/tcp": port for port in self.ports}, **{f"{port}/udp": port for port in self.ports}},
                            environment=self.env_vars,
                            volumes=self._build_volumes(),
                            detach=True,
                        )
                        self.running = True
                        self.set_state("running")
                        logging.info(f"{self.name} server container created and started.")
                        return f"{self.name} started"
                else:
                    logging.info(f"{self.name} is already running.")
                    return f"{self.name} is already running"
            elif command == "stop":
                if self.running:
                    container = self.client.containers.get(self.container_name)
                    self.set_state("stopping", "Saving and shutting down")
                    container.stop()
                    self.running = False
                    self.set_state("stopped")
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
            self.set_state("error", f"Docker error during {command}")
            return f"Error executing '{command}' on {self.name}"
        except Exception as e:
            logging.error(f"Unexpected error while executing '{command}' on {self.name}: {e}")
            self.set_state("error", f"Unexpected error during {command}")
            return f"Unexpected error: {e}"
        
    def pull_image(self) -> str:
        try:
            # Stream the pull so /update can show progress: bytes downloaded across layers, then bytes extracted.
            repo, tag = parse_repository_tag(self.image)
            downloaded: Dict[str, List[int]] = {}
            extracted: Dict[str, List[int]] = {}
            percent = 0
            for event in self.client.api.pull(repo, tag=tag or "latest", stream=True, decode=True):
                if "error" in event:
                    raise docker.errors.APIError(event["error"])
                layer, status = event.get("id"), event.get("status", "")
                detail = event.get("progressDetail") or {}
                if not layer:
                    continue
                if status == "Downloading" and detail.get("total"):
                    downloaded[layer] = [detail.get("current", 0), detail["total"]]
                elif status == "Download complete" and layer in downloaded:
                    downloaded[layer][0] = downloaded[layer][1]
                elif status == "Extracting" and detail.get("total"):
                    extracted[layer] = [detail.get("current", 0), detail["total"]]
                else:
                    continue
                if extracted:
                    phase, layers = "Unpacking Docker image", extracted
                else:
                    phase, layers = "Downloading Docker image", downloaded
                total = sum(t for _, t in layers.values())
                # Layer sizes arrive as each layer starts, so don't let the bar slide backwards within a phase.
                new_percent = int(100 * sum(c for c, _ in layers.values()) / total) if total else 0
                percent = new_percent if phase != self.detail else max(percent, new_percent)
                self.set_state("pulling", phase, min(percent, 100))
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
        Build a docker-py compatible volumes dict under the host path in self.volume.
          - If the image declares VOLUMEs, bind each one to the matching subdirectory of the host path
            (relative to the image's WorkingDir when it sits under it, e.g. Palworld's /opt/palworld/Pal/Saved -> <host>/Pal/Saved).
          - Otherwise bind the whole host path over the image's WorkingDir.
        Mounting over a WorkingDir that holds the game install (Palworld) hides it, so declared volumes win.
        Ensures host directories exist (os.makedirs(..., exist_ok=True)) to avoid Docker creating them as root.
        """
        vols: Dict[str, Dict[str, str]] = {}

        host_base_abs = os.path.abspath(self.volume)
        work_dir = self._get_image_working_dir()
        declared = self._get_image_volumes()
        if not declared:
            declared = [work_dir]
        uid = self._get_image_uid()
        for container_path in declared:
            rel = os.path.relpath(container_path, work_dir)
            if rel.startswith(".."):
                rel = container_path.lstrip("/")
            host_path = os.path.normpath(os.path.join(host_base_abs, rel))
            os.makedirs(host_path, exist_ok=True)
            # Images that run as a non-root user can't write to a fresh root-owned bind mount, so hand empty dirs to that user.
            if uid and not os.listdir(host_path):
                os.chown(host_path, uid, uid)
            vols[host_path] = {"bind": container_path, "mode": "rw"}
            logging.info(f"{self.name}: mounting {host_path} at {container_path}")
        return vols

    def _get_image_volumes(self) -> List[str]:
        try:
            return sorted((self.client.images.get(self.image).attrs['Config'].get('Volumes') or {}).keys())
        except Exception as e:
            logging.error(f"Couldn't read declared volumes of {self.image}: {e}")
            return []

    def _get_image_uid(self) -> int:
        # The image's USER as a numeric uid (0 when it runs as root or can't be resolved).
        try:
            user = (self.client.images.get(self.image).attrs['Config'].get('User') or "").split(":")[0]
            if not user or user == "root":
                return 0
            if user.isdigit():
                return int(user)
            out = self.client.containers.run(self.image, entrypoint=["id", "-u", user], remove=True)
            return int(out.decode().strip())
        except Exception as e:
            logging.error(f"Couldn't resolve the user of {self.image}: {e}")
            return 0

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
    {"EULA": "TRUE", "VERSION": "26.1"},
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
