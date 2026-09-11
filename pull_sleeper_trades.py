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
    print(f"Pulling trades for {year}...")
    all_transactions = []
    for week in range(1, 19):
        url = f"https://api.sleeper.app/v1/league/{league_id}/transactions/{week}"
        transactions = requests.get(url).json()
        trades = [t for t in transactions if t.get("type") == "trade"]
        all_transactions.extend(trades)

    with open(f"data/raw/sleeper/{year}_trades.json", "w") as f:
        json.dump(all_transactions, f, indent=2)

    print(f"  Found {len(all_transactions)} trades in {year}")

print("Done.")