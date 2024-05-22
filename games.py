import os
import keyboard
import time

def clear_terminal_inputs():
    keyboard.press_and_release("enter")
    time.sleep(1)

def parse_text(text):
    special_chars = {"~":"`","!":"1","@":"2","#":"3","$":"4","%":"5","^":"6","&":"7","*":"8","(":"9",")":"0","_":"-","+":"=","<":",",">":".","?":"/","{":"[",", }":"]","|":"\\"}
    for char in text:
        if char.isalpha() == True:
            if char.isupper() == True:
                char = char.lower()
                hotkey = "shift"
                keyboard.press_and_release(f"{hotkey}+" + char)
            else:
                keyboard.write(char)
                
        elif char in special_chars.keys():
            hotkey = "shift"
            keyboard.press_and_release(f"{hotkey}+" + special_chars[char])
        else:
            keyboard.write(char)

class GameServer:
    def __init__(self, name, port, path, log_file, cmds) -> None:
        self.name = name
        self.port = port
        self.path = path
        self.log_file = log_file
        self.cmds = cmds
        self.running = False

    def check_if_running(self):
        self.running = False
        os.system("sudo ps -ef > running_jobs.txt")
        f = open("running_jobs.txt", "r")
        file_contents = f.readlines()
        for line in file_contents:
            if self.cmds["launch"] in line:
                self.running = True
            else:
                pass

    def launch(self):
        self.check_if_running()
        if not self.running:
            print(f"{self.name} server not found, launching")
            clear_terminal_inputs()
            keyboard.write("cd " + self.path)
            keyboard.press_and_release("enter")
            self.exec_cmd("launch")
        else:
            print(f"{self.name} already running")

    def exec_cmd(self, command):
        clear_terminal_inputs()
        hotkeys = ["ctrl", "shift", "alt"]
        for key in hotkeys:
            if key in self.cmds[command]:
                hotkey = self.cmds[command].split(",")
                keyboard.press_and_release(f"{hotkey[0]}+{hotkey[1]}")
                return command
        keyboard.write(self.cmds[command])
        keyboard.press_and_release("enter")
        return command
game_list = []

minecraft_serv = GameServer("Minecraft", [25565], "/home/gameserver/minecraft/", {"file": "/home/gameserver/minecraft/logs/latest.log",  "connect": "joined the game", "disconnect": "left the game", "splice_start": 33}, {"launch": "java -jar server.jar nogui", "stop": "/stop", "test": "shift,s"})

game_list.append(minecraft_serv)