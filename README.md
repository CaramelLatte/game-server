# game-server

# game-server

A Python Flask-based API router for managing third-party game servers via Docker containers. Designed to run on a headless Linux server with modular expansion, real-time status tracking, and integration with a custom front-end UI all in mind.

**LIVE DEMO:**
https://www.caramellatte.dev/games

Please note that you will need to have the appropriate game installed to actually access any of the listed game servers.

## Setup
1. Clone the repo
2. Create a `.env` file with your Steam API key, SSL paths, and heartbeat URL
3. Run `python server.py`
*Ensure that you establish port forwarding for any game you wish to run through this server manager. See the GameServer class in games.py to see what these ports are for existing games, and how you expose them to your containers should you wish to add your own containers.

## Usage
- The server listens for HTTP requests at defined endpoints
- Pair with a front-end to visualize server status and issue commands. To establish a quick and dirty way to interface with this server manager without first building a front-end UI, you may also simply direct your browser to the appropriate endpoints 'e.g. https://{local ip or domain name.tld}:{ip you set server to listen to, default 8080}/{gameid}/{cmd} or set up a post manager like postman or insomnia with the correct URLs to manually target endpoints.


Adding new games is simple. In games.py, create a new instance of the GameServer object in the same style as the existing variables. The attributes of this object must be edited to match the specifics of the game name, port, path to executable, path to log file, identifying string flags for connection/disconnection messages (used to parse a list of connected users), and the commands you want to be able to issue to the process. You can add additional commands beyond what is shown, however you will also need to add logic to handle those commands as presently any commands other than 'start' and 'stop' reach an 'unknown command' error handling state.

CHANGES PLANNED:

1: **Implement API key checking to only allow validated users to issue commands**
  While this is intended and makes sense for a production version of this software, it doesn't make sense to incorporate this functionality while this project simply operates on my own personal hardware as a demonstration for my portfolio.

2: **Consider using personally-build docker containers to allow consistent performance across different game servers**
  Different docker containers built by different developers will have different capabilities and features. This makes coding a single clean set of logic to handle all possible games a user might want to add exceptionally difficult. As an example, some docker containers will correctly see changes made to the mirrored easily-accessible directories, and some will only reference an internally-managed hashed directory in /var/lib/docker/volumes/ despite every server object being created with a valid defined mirror volume. This makes it unintuitive and complicated to figure out how to modify and customize a game server at the user's whim. There may be additional ways to resolve this that I can explore, but this is of lesser priority than just further refining my development skills.

3: **Refactoring**
  There is likely a lot left to do here as this project has essentially been iterated upon from near the beginning of my development learning, so I revisit and improve upon it over time.

4: **Expand these servers with mod support**
  Along with building my own containers, having a method to allow for third party mods to be incorporated into an image drastically improves replayability and appeal factor for certain users. This is an extensive undertaking that I believe will require significant time investment, as mods are handled a variety of ways for different games, and they would all require creating custom images. Still, it would be really dang cool to have this feature.

5: **Features to back-up and create new instances of an image, or of the data within**
  The types of games suited to this project largely are cooperative or competitive with instanced worlds that users may play in together. It would be particularly nice if, for instance, one group of friends may create an instance of a world and keep their own progress and state separate from another group of friends, allowing a wider array of users to utilize the same server manager.
  
