import os
import requests
import logging
import dotenv

logging.basicConfig(level=logging.WARNING)

def get_steam_username(steam_id):
    #Fetches the Steam username for a given Steam ID using the Steam API.
    
    # Check if the API key is set in the environment variables
    api_key= os.getenv("STEAM_API_KEY")
    if not api_key:
        raise ValueError("Steam API key not found. Please set the STEAM_API_KEY environment variable.")
    
    
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
    response = requests.get(url)
    data = response.json()
    
    if data['response']['players']:
        return data['response']['players'][0]['personaname']
    else:
        logging.warning(f"Could not resolve Steam ID {steam_id} to a username. Keeping the numeric ID as the player name.")
        return None
