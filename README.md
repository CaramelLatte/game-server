# game-server

Python Flask router that uses emulated keystrokes to automate and manage third-party game servers. 

How to use:
Server is built to listen to specific end-points for HTTP requests, and execute specific functions depending on which end-point a user reaches. The intended use is to pair with a webpage to issue requests to the servers endpoints.

Adding new games is simple. In games.py, create a new instance of the GameServer object in the same style as the demo variable 'minecraft_serv'. The attributes of this object must be edited to match the specifics of the game name, port, path to executable, path to log file, identifying string flags for connection/disconnection messages (used to parse a list of connected users), and the commands you want to be able to issue to the process. You can add additional commands beyond what is shown.