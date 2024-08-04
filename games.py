import os
import keyboard
import time

def clear_terminal_inputs():
    keyboard.press_and_release("enter")
    time.sleep(1)

#Keyboard module is used to emulate key presses to send commands to already-active terminal processes. Because emulated keys for capital letters and characters accessed by shift key don't physically exist on keyboard, this function can be used to enter special characters if necessary.
#CURRENTLY DOES NOT WORK IN LINUX ENVIRONMENT - Observed behavior is that using the shift key through the keyboard module in Linux will result in locking keyboard inputs into the shift layer, which breaks all further inputs. Unsure if this is a fixable bug or a limitation of the module.
def parse_text(text):
    special_chars = {"~":"`","!":"1","@":"2","#":"3","$":"4","%":"5","^":"6","&":"7","*":"8","(":"9",")":"0","_":"-","+":"=","<":",",">":".","?":"/","{":"[",", }":"]","|":"\\"}
    for char in text:
        if char.isalpha() == True and char.isupper() == True:
            if char.isupper() == True:
                char = char.lower()
                keyboard.press_and_release(f"shift+{char}")
        elif char in special_chars.keys():
            keyboard.press_and_release(f"shift+{special_chars[char]}")
        else:
            keyboard.write(char)
#GameServer class is used to store information about game servers, such as name(string), icon(filename string sans extension), ports(list), path(string), log file(string), and commands to start and stop the server. Additional commands may be added to any individual game server to make use of functionality made available through that game's own server software.
# 
# The class also has a method to check if the server is running, and a method to execute a command on the server. 
class GameServer:
    def __init__(self, name, icon, port, path, log_file, cmds) -> None:
        self.name = name #String, name of the game server
        self.icon = icon #string, filename sans extension of the game server icon
        self.ports = port #List, ports used by the game server. This is used to check if the port is listening to determine if the server is running.
        self.path = path #string, path to the game server's main directory
        self.log_file = log_file #dictionary, contains information about the game server's log file, including the file path, the string that indicates a player has connected, the string that indicates a player has disconnected, and the splice points to extract the player name from the log file. 
        self.cmds = cmds #dictionary, contains the commands to start and stop the game server. Additional commands may be added to this dictionary to make use of additional functionality provided by the game server software. The start command may be either a single string or a list of strings, this is used to start a server in the instance where a single command is impractical.
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
        if type(self.cmds[command]) == list:
            for cmd in self.cmds[command]:
                parse_text(cmd)
                keyboard.press_and_release("enter")
        else:
            parse_text(self.cmds[command])
        keyboard.press_and_release("enter")
        return command

#Define the game list and add individual game server objects to it. Refer to the GameServer class for more information on the parameters required to create a new game server object.
game_list = []

minecraft_serv = GameServer("Minecraft", "minecraft", [25565], "/home/gameserver/minecraft/", {"file": "/home/gameserver/minecraft/logs/latest.log",  "connect": "joined the game", "disconnect": "left the game", "splice_join_start": 33, "splice_left_start": 33, "splice_join_end": -13, "splice_left_end": -13}, {"start": "java -jar server.jar nogui", "stop": "/stop"})
val_serv = GameServer("Valheim", "valheim", [2456, 2457], "/home/gameserver/valheim/", {"file": "/home/gameserver/valheim/valheim_log.txt", "connect": "Got handshake from client", "disconnect": "Closing socket", "splice_join_start": 47, "splice_left_start": 36, "splice_join_end": 64, "splice_left_end": 53}, {"start": ". start-server.sh", "stop": "ctrl,c"})
seven_days_serv = GameServer("7 Days to Die", "7days", [26900,26901,26902], "/home/gameserver/7-days-to-die/", {"file": "/home/gameserver/7-days-to-die/log.txt", "connect": "' joined the game", "disconnect":"' left the game", "splice_join_start": 49, "splice_left_start": 49, "splice_join_end": -14, "splice_left_end": -14}, {"start": ". startserver.sh -configfile='serverconfig.xml'", "stop" : "ctrl,c"})
pal_server = GameServer("Palworld", "palworld", [8211], "/home/gameserver/palworld/", {"file" : "/home/gameserver/palworld/log.txt", "connect": "joined the server.", "disconnect": "left the server.", "splice_join_start": 28, "splice_left_start": 28, "splice_join_end": -54, "splice_left_end": -52}, {"start": ["cp /home/gameserver/palworld/DefaultPalWorldSettings.old.ini /home/gameserver/palworld/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini ",". palserver.sh"], "stop": "ctrl,c"})
game_list.append(minecraft_serv)
game_list.append(val_serv)
game_list.append(seven_days_serv)
game_list.append(pal_server)