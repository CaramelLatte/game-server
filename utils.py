import os
import requests
import logging

STEAM_SUMMARIES_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"

def get_steam_username(steam_id):
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        logging.warning("STEAM_API_KEY is not set; skipping Steam name lookup.")
        return None
    try:
        response = requests.get(
            STEAM_SUMMARIES_URL,
            params={"key": api_key, "steamids": steam_id},
            timeout=5,
        )
        response.raise_for_status()
        players = response.json().get("response", {}).get("players", [])
        if players:
            return players[0]["personaname"]
        logging.warning(f"Steam returned no player for ID {steam_id}.")
    # Never log the exception text from requests: it includes the full URL, API key and all.
    except requests.exceptions.HTTPError as e:
        logging.error(f"Steam API returned HTTP {e.response.status_code} for ID {steam_id}.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Steam API request failed for ID {steam_id}: {type(e).__name__}")
    except (KeyError, ValueError) as e:
        logging.error(f"Unexpected Steam API response for ID {steam_id}: {type(e).__name__}")
    return None
