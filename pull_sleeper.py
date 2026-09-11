import requests
import json
import os

seasons = {
    "2023": "994110786538692608",
    "2024": "1073712936624959488",
    "2025": "1180198165768134656",
    "2026": "1314327003792445440"
}

os.makedirs("data/raw/sleeper", exist_ok=True)

for year, league_id in seasons.items():
    print(f"Pulling {year}...")

    league = requests.get(f"https://api.sleeper.app/v1/league/{league_id}").json()
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()

    with open(f"data/raw/sleeper/{year}_league.json", "w") as f:
        json.dump(league, f, indent=2)

    with open(f"data/raw/sleeper/{year}_rosters.json", "w") as f:
        json.dump(rosters, f, indent=2)

    with open(f"data/raw/sleeper/{year}_users.json", "w") as f:
        json.dump(users, f, indent=2)

    print(f"Saved {year}")

print("Done with all seasons.")