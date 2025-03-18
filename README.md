# game-server

Python Flask router that uses emulated keystrokes to automate and manage third-party game servers. 

HOW TO USE:
Server is built to listen to specific end-points for HTTP requests, and execute specific functions depending on which end-point a user reaches. The intended use is to pair with a webpage to issue requests to the servers endpoints.

Adding new games is simple. In games.py, create a new instance of the GameServer object in the same style as the demo variable 'minecraft_serv'. The attributes of this object must be edited to match the specifics of the game name, port, path to executable, path to log file, identifying string flags for connection/disconnection messages (used to parse a list of connected users), and the commands you want to be able to issue to the process. You can add additional commands beyond what is shown.

CHANGES PLANNED:

1: Implement API key checking to only allow validated users to issue commands


2: Consider changing server management to using docker containers -
Pros:
- Easier maintenance and updating of individual servers
- Adding new games becomes simpler - as long as a docker container exists, downloading it and adding the relevant entries to games.py will be sufficient
- No further logic needed to handle running servers that require wine or other special dependancies - docker will automate this as part of its build process

Cons:
- Docker containers tend to have significantly longer startup times than operating files sitting on the bare file system. This leads to a worse user experience. As a comparison, operating a docker container can take between five and twenty minutes while dependencies are downloaded and set up each time the container is started, whereas this current implementation typically takes a minute or less to go from no active server to the user's server of choice being accessible.
- Previous experience has shown that persistent storage can be problematic. As an example of this, a test with a docker container for V Rising resulted in saved data being lost on every container restart. If this problem ends up being more common with docker containers, additional functions to automatically back-up save data will be required to handle it. It is possible that this can be resolved by modifying the containers themselves to suit my needs, but more research is required.

3: Refactoring:
- Improve exception handling in the instance that server cannot be started
- Change SSL certs from hard-coded paths to environment variables for security
- Give a sweeping pass to error handling
- Server uses a lot of global variables as a quick and dirty way to get things working during initial project coding. It would be better to wrap these into a state object, both for readability and error resilience.


GAMES TO ADD:
V Rising
Enshrouded
