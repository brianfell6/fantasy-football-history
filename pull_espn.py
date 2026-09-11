import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

league_id = "1334324"
cookies = {
    "espn_s2": os.environ["ESPN_S2"],
    "SWID": os.environ["ESPN_SWID"]
}

os.makedirs("data/raw/espn", exist_ok=True)

years_current_format = [2018, 2019, 2021, 2022]
years_legacy_format = [2017]
skip_years = [2020]

all_views = ["mTeam", "mMatchup", "mStandings", "mSettings", "mTransactions2", "mDraftDetail"]

for year in years_current_format:
    print(f"Pulling {year}...")
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}"
    params = {"view": all_views}
    response = requests.get(url, cookies=cookies, params=params)
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        with open(f"data/raw/espn/{year}.json", "w") as f:
            json.dump(response.json(), f, indent=2)
        print(f"  Saved {year}")
    else:
        print(f"  Failed to pull {year}")

for year in years_legacy_format:
    print(f"Pulling {year} (legacy format)...")
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}"
    params = {"seasonId": year, "view": all_views}
    response = requests.get(url, cookies=cookies, params=params)
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        with open(f"data/raw/espn/{year}.json", "w") as f:
            json.dump(response.json(), f, indent=2)
        print(f"  Saved {year}")
    else:
        print(f"  Failed to pull {year}")

print(f"Skipped years (no data): {skip_years}")
print("Done with all ESPN seasons.")