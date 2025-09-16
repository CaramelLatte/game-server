import os
import requests
import logging

logging.basicConfig(level=logging.WARNING)

def get_steam_username(steam_id):
    try:
        api_key = os.getenv("STEAM_API_KEY")
        if not api_key:
            raise ValueError("Steam API key not found. Please set the STEAM_API_KEY environment variable.")
        url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data['response']['players']:
            return data['response']['players'][0]['personaname']
        else:
            logging.warning(f"Could not resolve Steam ID {steam_id} to a username. Keeping the numeric ID as the player name.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Steam username for ID {steam_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in get_steam_username: {e}")
        return None
