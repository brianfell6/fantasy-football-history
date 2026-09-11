import requests
import json
import os

seasons = {
    "2023": "994110786538692608",
    "2024": "1073712936624959488",
    "2025": "1180198165768134656"
}

os.makedirs("data/raw/sleeper", exist_ok=True)

for year, league_id in seasons.items():
    print(f"Pulling bracket for {year}...")
    bracket = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/winners_bracket").json()
    with open(f"data/raw/sleeper/{year}_bracket.json", "w") as f:
        json.dump(bracket, f, indent=2)
    print(f"  Saved {year}")

print("Done.")