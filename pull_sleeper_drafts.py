import requests
import json

seasons_draft_ids = {}

for year in ["2023", "2024", "2025", "2026"]:
    with open(f"data/raw/sleeper/{year}_league.json") as f:
        league = json.load(f)
    seasons_draft_ids[year] = league["draft_id"]

print(seasons_draft_ids)

for year, draft_id in seasons_draft_ids.items():
    print(f"Pulling draft {year} (draft_id: {draft_id})...")

    draft_info = requests.get(f"https://api.sleeper.app/v1/draft/{draft_id}").json()
    picks = requests.get(f"https://api.sleeper.app/v1/draft/{draft_id}/picks").json()

    with open(f"data/raw/sleeper/{year}_draft_info.json", "w") as f:
        json.dump(draft_info, f, indent=2)

    with open(f"data/raw/sleeper/{year}_draft_picks.json", "w") as f:
        json.dump(picks, f, indent=2)

    print(f"  Saved {len(picks)} picks")

print("Done.")