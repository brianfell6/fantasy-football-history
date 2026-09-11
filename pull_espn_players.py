import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

cookies = {
    "espn_s2": os.environ["ESPN_S2"],
    "SWID": os.environ["ESPN_SWID"]
}

headers = {
    "x-fantasy-filter": json.dumps({
        "players": {
            "limit": 3000,
            "sortPercOwned": {"sortAsc": False, "sortPriority": 1}
        }
    })
}

url = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2022/players"
params = {"view": "players_wl"}

print("Pulling ESPN's full player list...")
response = requests.get(url, cookies=cookies, headers=headers, params=params)
data = response.json()

player_lookup = {}
skipped = 0
for p in data:
    name = p.get("fullName")
    if not name:
        first = p.get("firstName", "")
        last = p.get("lastName", "")
        name = f"{first} {last}".strip()
    if not name:
        skipped += 1
        continue
    player_lookup[p["id"]] = name

with open("data/raw/espn/players.json", "w") as f:
    json.dump(player_lookup, f)

print(f"Saved {len(player_lookup)} players ({skipped} skipped with no name at all).")