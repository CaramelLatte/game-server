import docker
import os
import requests

def get_steam_username(steam_id, api_key):
    #Fetches the Steam username for a given Steam ID using the Steam API.
    
    # Check if the API key is set in the environment variables
    api_key= os.getenv("STEAM_API_KEY")
    if not api_key:
        raise ValueError("Steam API key not found. Please set the STEAM_API_KEY environment variable.")
    
    
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
    response = requests.get(url)
    data = response.json()
    
    if data['response']['players']:
        return data['response']['players'][0]['personaname']
    else:
        return None

class GameServer:
    def __init__(self, name, icon, ports, image, container_name, env_vars=None, volume=None, log_strings=None) -> None:
        self.name = name  # String, name of the game server
        self.icon = icon  # String, filename sans extension of the game server icon
        self.ports = ports  # List, ports used by the game server
        self.image = image  # String, Docker image name
        self.container_name = container_name  # String, Docker container name
        self.env_vars = env_vars or {}  # Dictionary, environment variables for the container
        self.volume = volume  # String, directory path to mount. The container will have its own working directory, we set an additional path to mount here to allow for files to persist between server restarts.
        self.log_strings = log_strings # Dictionary, log strings for player connection/disconnection, as well as a line to indicate a new instance of server has been launched
        # Important note - if the server log line ends with the player name for connect, disconnect, or both, there is no tail to check for. In this case, the tail should be set to an empty string.
        self.running = False 
        self.client = docker.from_env() # Initialize Docker client

    def get_connected_players(self):
        # Fetches the list of connected players from the game server logs.
        # This method uses the log strings defined in the log_strings dictionary to parse the logs and extract player names.
        if not self.log_strings:
            return []
        connected_players = []
        container = self.client.containers.get(self.container_name)
        logs = container.logs(stream=False)
        if logs:
            log_lines = logs.decode('utf-8').split('\n')
            
            # Log files are persistent across container restarts, so we use a string generated early in the server's lifetime to determine if the server has been restarted, so that we can clear old player names from the list.
            # This is a workaround to handle instances of players connecting previously, with no associated disconnection events logged, in the case of a server shutdown.
            for line in log_lines:
                if self.log_strings["new_instance"] in line:
                    for player in connected_players:
                        connected_players.remove(player)

                # Check for player connection and disconnection events. We use string slicing to extract the player name from the log line between the connect/disconnect head/tail strings.
                # In instances where there is no tail to check (the server log line ends with player name, with nothing to handle as a tail), we check for the head string only, and slice the line from the head string to the end of the line.
                if len(self.log_strings["connect_tail"]) == 0:
                    if self.log_strings["connect_head"] in line:
                        start = line.index(self.log_strings["connect_head"]) + len(self.log_strings["connect_head"])
                        player_name = line[start:].strip()
                        connected_players.append(player_name)
                elif self.log_strings["connect_head"] in line and self.log_strings["connect_tail"] in line:
                    start = line.index(self.log_strings["connect_head"]) + len(self.log_strings["connect_head"])
                    end = line.index(self.log_strings["connect_tail"])
                    player_name = line[start:end].strip()
                    connected_players.append(player_name)

                if len(self.log_strings["disconnect_tail"]) == 0:
                    if self.log_strings["disconnect_head"] in line:
                        start = line.index(self.log_strings["disconnect_head"]) + len(self.log_strings["disconnect_head"])
                        player_name = line[start:].strip()
                        connected_players.remove(player_name) if player_name in connected_players else None
                elif self.log_strings["disconnect_head"] in line and self.log_strings["disconnect_tail"] in line:
                    start = line.index(self.log_strings["disconnect_head"]) + len(self.log_strings["disconnect_head"])
                    end = line.index(self.log_strings["disconnect_tail"])
                    player_name = line[start:end].strip()
                    connected_players.remove(player_name) if player_name in connected_players else None
        #Check for steamIDs in the connected players list, and replace them with the corresponding steam usernames using the Steam API.
        for player in connected_players:
            if player.isdigit():
                steam_username = get_steam_username(player, os.getenv("STEAM_API_KEY"))
                if steam_username:
                    connected_players[connected_players.index(player)] = steam_username
                else:
                    pass
        return connected_players

    def check_if_running(self):
        try:
            container = self.client.containers.get(self.container_name)
            self.running = container.status == "running"
        except docker.errors.NotFound:
            self.running = False
            

    def exec_cmd(self, command):
        self.check_if_running()
        if command == "start":
            if not self.running:
                try:
                    # Check if the container already exists
                    container = self.client.containers.get(self.container_name)
                    # Start the existing container
                    container.start()
                    return f"{self.name} started"
                except docker.errors.NotFound:
                    # If the container doesn't exist, check if the image exists and pull it if not
                    images = self.client.images.list(name=self.image)
                    if not images:
                        self.client.images.pull(self.image)

                    # Create and start a new container with associated arguments
                    self.client.containers.run(
                        self.image,
                        name=self.container_name,
                        ports={
                            # Here we bind both TCP and UDP ports, to handle instances where a server utilizes both protocols (7 days to die does this, as an example)
                            **{f"{port}/tcp": port for port in self.ports},
                            **{f"{port}/udp": port for port in self.ports}
                        },
                        environment=self.env_vars,
                        volumes={
                            self.volume: {
                                'bind': '/data',  # Target path in container
                                'mode': 'rw'  # Read-write mode
                            }
                        },
                        detach=True,
                    )
                    return f"{self.name} started"
            else:
                return f"{self.name} is already running"
        elif command == "stop":
            if self.running:
                # Stop the container without removing it
                container = self.client.containers.get(self.container_name)
                container.stop()
                return f"{self.name} stopped"
            else:
                return f"{self.name} is not running"
        else:
            # Placeholder, more commands can be added using docker exec to run commands inside the container.
            # For example, you could add additional commands for each game server, like toggling weather effects in Minecraft or changing the game mode in Valheim.
            return f"Unknown command: {command}"
        


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
    }
)
val_serv = GameServer(
    "Valheim",
    "valheim",
    [2456, 2457],
    "lloesche/valheim-server",
    "valheim_server",
    {"SERVER_NAME": "ValheimServer", "WORLD_NAME": "MyWorld", "SERVER_PASS": "secret"},
    "/home/gameserver/valheim/",
    {
        "connect_head": "Got handshake from client ",
        "connect_tail": "",
        "disconnect_head": "Closing socket ",
        "disconnect_tail": "",
        "new_instance": "Starting Valheim server",
    }
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
    }
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
    }
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
    }
)

terraria_serv = GameServer(
    "Terraria",
    "terraria",
    [7777],
    "delath/terraria",
    "terraria_server",
    {},
    "/home/gameserver/terraria/",
    {
    }
)

game_list.append(minecraft_serv)
game_list.append(val_serv)
game_list.append(seven_days_serv)
game_list.append(pal_server)
game_list.append(vrising_serv)
game_list.append(terraria_serv)
#PERSONAL NOTE: persistent data for these servers is stored at /var/lib/docker/volumes/, from here you can find the correct directory to enter by doing ls -lt, the optional flag to sort by date. When changing settings on a server, change them this way instead of the mirrored directory defined in the server object