import docker
import os

class GameServer:
    def __init__(self, name, icon, ports, image, container_name, env_vars=None, volume=None) -> None:
        self.name = name  # String, name of the game server
        self.icon = icon  # String, filename sans extension of the game server icon
        self.ports = ports  # List, ports used by the game server
        self.image = image  # String, Docker image name
        self.container_name = container_name  # String, Docker container name
        self.env_vars = env_vars or {}  # Dictionary, environment variables for the container
        self.volume = volume  # String, Docker volume for persistent storage
        self.running = False
        self.client = docker.from_env()

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

                # host_path = os.path.abspath("./mc_test").replace('\\', '/')
                self.client.containers.run(
                    self.image,
                    name=self.container_name,
                    ports={f"{port}/tcp": port for port in self.ports},
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
    "itzg/minecraft-server",
    "minecraft_server",
    {"EULA": "TRUE"},
    "/home/gameserver/minecraft/"
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
    "7days_server"
    {},
    "/home/gameserver/minecraft/"
)
pal_server = GameServer(
    "Palworld",
    "palworld",
    [8211],
    "palworld/server-image",
    "palworld_server",
    {},
    "/home/gameserver/palworld/"
)

game_list.append(minecraft_serv)
game_list.append(val_serv)
game_list.append(seven_days_serv)
game_list.append(pal_server)