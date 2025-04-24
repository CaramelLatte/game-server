import docker
import os

class GameServer:
    def __init__(self, name, icon, ports, protocol, image, container_name, env_vars=None, volume=None, log_params={}) -> None:
        self.name = name  # String, name of the game server
        self.icon = icon  # String, filename sans extension of the game server icon
        self.ports = ports  # List, ports used by the game server
        self.protocol = protocol # String, protocol used by the game server (e.g., "tcp", "udp")
        self.image = image  # String, Docker image name
        self.container_name = container_name  # String, Docker container name
        self.env_vars = env_vars or {}  # Dictionary, environment variables for the container
        self.volume = volume  # String, Docker volume for persistent storage
        self.log_params = log_params
        self.running = False
        self.client = docker.from_env()

    def get_connected_players(self):
        connected_players = []
        container = self.client.containers.get(self.container_name)
        logs = container.logs(stream=False)
        for line in logs.decode('utf-8').splitlines():
            if self.log_params["connect"] in line:
                parsed_name = line[self.log_params["splice_join_start"]:self.log_params["splice_join_end"]]
                if parsed_name not in connected_players:
                    connected_players.append(parsed_name)
            elif self.log_params["disconnect"] in line:
                parsed_name = line[self.log_params["splice_left_start"]:self.log_params["splice_left_end"]]
                if parsed_name in connected_players:
                    connected_players.remove(parsed_name)
        return []

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

                self.client.containers.run(
                    self.image,
                    name=self.container_name,
                    ports={f"{port}/{self.protocol}": port for port in self.ports},
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
                container = self.client.containers.get(self.container_name)
                container.stop()
                container.remove()
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
    "tcp",
    "itzg/minecraft-server",
    "minecraft_server",
    {"EULA": "TRUE"},
    "/home/gameserver/minecraft/",
    {
        "connect": "joined the game",
        "disconnect": "left the game",
        "splice_join_start": 33,
        "splice_left_start": 33,
        "splice_join_end": -13,
        "splice_left_end": -13
    }
)
val_serv = GameServer(
    "Valheim",
    "valheim",
    [2456, 2457],
    "udp",
    "lloesche/valheim-server",
    "valheim_server",
    {"SERVER_NAME": "ValheimServer", "WORLD_NAME": "MyWorld", "SERVER_PASS": "secret"},
    "/home/gameserver/valheim/"
)
seven_days_serv = GameServer(
    "7 Days to Die",
    "7days",
    [26900, 26901, 26902],
    "tcp",
    "didstopia/7dtd-server",
    "7days_server",
    {},
    "/home/gameserver/minecraft/"
)
pal_server = GameServer(
    "Palworld",
    "palworld",
    [8211],
    "tcp",
    "palworld/server-image",
    "palworld_server",
    {},
    "/home/gameserver/palworld/"
)

game_list.append(minecraft_serv)
game_list.append(val_serv)
game_list.append(seven_days_serv)
game_list.append(pal_server)