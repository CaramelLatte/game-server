import os
import keyboard
import time

def clear_terminal_inputs():
    keyboard.press_and_release("enter")
    time.sleep(1)

#Keyboard module is used to emulate key presses to send commands to already-active terminal processes. Because emulated keys for capital letters and characters accessed by shift key don't physically exist on keyboard, this function can be used to enter special characters if necessary.
def parse_text(text):
    special_chars = {"~":"`","!":"1","@":"2","#":"3","$":"4","%":"5","^":"6","&":"7","*":"8","(":"9",")":"0","_":"-","+":"=","<":",",">":".","?":"/","{":"[",", }":"]","|":"\\"}
    for char in text:
        if char.isalpha() == True and char.isupper() == True:
            if char.isupper() == True:
                char = char.lower()
                keyboard.press_and_release(f"shift+{char}")
        elif char in special_chars.keys():
            keyboard.press("shift")
            keyboard.press(char)
            keyboard.release("shift")
        else:
            keyboard.write(char)

class GameServer:
    def __init__(self, name, icon, port, path, log_file, cmds) -> None:
        self.name = name
        self.icon = icon
        self.ports = port
        self.path = path
        self.log_file = log_file
        self.cmds = cmds
        self.running = False

    def check_if_running(self):
        self.running = False
        os.system("ss -l > running_jobs.txt")
        f = open("running_jobs.txt", "r")
        file_contents = f.readlines()
        for line in file_contents:
            for port in self.ports:
                if str(port) in line:
                    self.running = True
                else:
                    pass

    def exec_cmd(self, command):
        clear_terminal_inputs()
        if command == "start":
            self.check_if_running()
            if not self.running:
                keyboard.write("cd " + self.path)
                keyboard.press_and_release("enter")
            else:
                return (f"{self.name} already running")
        hotkeys = ["ctrl", "shift", "alt"]
        for key in hotkeys:
            if key in self.cmds[command]:
                hotkey = self.cmds[command].split(",")
                keyboard.press_and_release(f"{hotkey[0]}+{hotkey[1]}")
                return command
        parse_text(self.cmds[command])
        keyboard.press_and_release("enter")
        return command
    
game_list = []

minecraft_serv = GameServer("Minecraft", "minecraft", [25565], "/home/gameserver/minecraft/", {"file": "/home/gameserver/minecraft/logs/latest.log",  "connect": "joined the game", "disconnect": "left the game", "splice_start": 33}, {"start": "java -jar server.jar nogui", "stop": "/stop"})
val_serv = GameServer("Valheim", "valheim", [2456, 2457], "/home/gameserver/valheim/", {"file": "/home/gameserver/valheim/valheim_log.txt", "connect": "Got handshake from client", "disconnect": "Closing socket", "splice_start": 20}, {"start": ". start-server.sh", "stop": "ctrl,c"})
seven_days_serv = GameServer("7 Days to Die", "7days", [26900,26901,26902], "/home/gameserver/7-days-to-die/", {"file": "/home/gameserver/7-days-to-die/log.txt", "connect": "' joined the game", "disconnect":"' left the game", "splice_start": 46}, {"start": ". startserver.sh -configfile='serverconfig.xml'", "stop" : "ctrl,c"})
pal_server = GameServer("Palworld", "palworld", [8211], "/home/gameserver/palworld/", {"file" : None, "connect": None, "disconnect": None, "splice_start": 0}, {"start": ". palserver.sh", "stop": "ctrl,c"})
game_list.append(minecraft_serv)
game_list.append(val_serv)
game_list.append(seven_days_serv)
game_list.append(pal_server)