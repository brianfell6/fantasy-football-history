import requests
import json

print("Pulling Sleeper's full player list (this is a large file, may take a moment)...")
players = requests.get("https://api.sleeper.app/v1/players/nfl").json()

with open("data/raw/sleeper/players.json", "w") as f:
    json.dump(players, f)

print(f"Saved {len(players)} players.")