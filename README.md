# game-server

Python Flask router that uses emulated keystrokes to automate and manage third-party game servers. 

How to use:
Server is built to listen to specific end-points for HTTP requests, and execute specific functions depending on which end-point a user reaches. The intended use is to pair with a webpage to issue requests to the servers endpoints.

Adding new games is simple. In games.py, create a new instance of the GameServer object in the same style as the demo variable 'minecraft_serv'. The attributes of this object must be edited to match the specifics of the game name, port, path to executable, path to log file, identifying string flags for connection/disconnection messages (used to parse a list of connected users), and the commands you want to be able to issue to the process. You can add additional commands beyond what is shown.

Changes planned:

implement API key checking to only allow validated users to issue commands

Consider changing server management to using docker containers -
Pros:
- Easier maintenance and updating of individual servers
- Adding new games becomes simpler - as long as a docker container exists, downloading it and adding the relevant entries to games.py will be sufficient
- No further logic needed to handle running servers that require wine or other special dependancies - docker will automate this as part of its build process

Cons:
- Docker containers tend to have longer startup times than operating files sitting on the bare file system. This leads to a worse user experience and more resource consumption.
- Previous experience has shown that persistent storage can be problematic if containers are not set up properly. As an example of this, a test with a docker container for V Rising resulted in saved data being lost on every container restart. If this problem ends up being more common with docker containers, additional functions to automatically back-up save data will be required to handle it.

Games to add:
V Rising
Palworld
Enshrouded