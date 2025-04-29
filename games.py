import docker
import os

class GameServer:
    def __init__(self, name, icon, ports, image, container_name, env_vars=None, volume=None, log_strings=None) -> None:
        self.name = name  # String, name of the game server
        self.icon = icon  # String, filename sans extension of the game server icon
        self.ports = ports  # List, ports used by the game server
        self.image = image  # String, Docker image name
        self.container_name = container_name  # String, Docker container name
        self.env_vars = env_vars or {}  # Dictionary, environment variables for the container
        self.volume = volume  # String, Docker volume for persistent storage
        self.log_strings = log_strings
        self.running = False
        self.client = docker.from_env()

    def get_connected_players(self):
        if not self.log_strings:
            return []
        connected_players = []
        container = self.client.containers.get(self.container_name)
        logs = container.logs(stream=False)
        if logs:
            log_lines = logs.decode('utf-8').split('\n')
            for line in log_lines:
                if "Running as user: docker" in line:
                    for player in connected_players:
                        connected_players.remove(player)
                if self.log_strings["connect_head"] in line and self.log_strings["connect_tail"] in line:
                    start = line.index(self.log_strings["connect_head"]) + len(self.log_strings["connect_head"])
                    end = line.index(self.log_strings["connect_tail"])
                    player_name = line[start:end].strip()
                    connected_players.append(player_name)
                elif self.log_strings["disconnect_head"] in line and self.log_strings["disconnect_tail"] in line:
                    start = line.index(self.log_strings["disconnect_head"]) + len(self.log_strings["disconnect_head"])
                    end = line.index(self.log_strings["disconnect_tail"])
                    player_name = line[start:end].strip()
                    connected_players.remove(player_name) if player_name in connected_players else None
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

                    # Create and start a new container
                    self.client.containers.run(
                        self.image,
                        name=self.container_name,
                        ports={
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
            return f"Unknown command: {command}"
        


# Define the game list and add individual game server objects to it
game_list = []

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
    }
)
val_serv = GameServer(
    "Valheim",
    "valheim",
    [2456, 2457],
    "lloesche/valheim-server",
    "valheim_server",
    {"SERVER_NAME": "ValheimServer", "WORLD_NAME": "MyWorld", "SERVER_PASS": "secret"},
    "/home/gameserver/valheim/"
)
seven_days_serv = GameServer(
    "7 Days to Die",
    "7days",
    [26900, 26901, 26902],
    "didstopia/7dtd-server",
    "7days_server",
    {},
    "/home/gameserver/7-days-to-die/",
    {
        "connect_head": "GMSG: Player '",
        "connect_tail": "' joined the game",
        "disconnect_head": "GMSG: Player '",
        "disconnect_tail": "' left the game",
    }
)
pal_server = GameServer(
    "Palworld",
    "palworld",
    [8211],
    "kagurazakanyaa/palworld",
    "palworld_server",
    {},
    "/home/gameserver/palworld/"
)

game_list.append(minecraft_serv)
game_list.append(val_serv)
game_list.append(seven_days_serv)
game_list.append(pal_server)