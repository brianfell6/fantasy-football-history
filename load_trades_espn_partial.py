import json
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("ALTER TABLE trades ADD COLUMN IF NOT EXISTS is_partial BOOLEAN DEFAULT FALSE;")
conn.commit()

cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'espn';")
espn_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}

cursor.execute("SELECT season_id, year FROM seasons WHERE platform = 'espn';")
espn_season_lookup = {year: season_id for season_id, year in cursor.fetchall()}

years = ["2017", "2018", "2019", "2021", "2022"]

for year in years:
    print(f"Processing ESPN trade-acquired players for {year}...")

    with open(f"data/raw/espn/{year}.json") as f:
        raw = json.load(f)
    data = raw[0] if year == "2017" else raw

    season_id = espn_season_lookup.get(int(year))

    # Group trade-acquired entries by acquisitionDate
    groups = {}
    for team in data.get("teams", []):
        owners = team.get("owners", [])
        if not owners:
            continue
        espn_member_id = owners[0].strip("{}")
        owner_id = espn_id_to_owner.get(espn_member_id)

        for entry in team.get("roster", {}).get("entries", []):
            if entry.get("acquisitionType") == "TRADE":
                date = entry.get("acquisitionDate")
                player_name = entry["playerPoolEntry"]["player"]["fullName"]
                groups.setdefault(date, []).append({
                    "owner_id": owner_id,
                    "player": player_name
                })

    for date, items in groups.items():
        traded_at = datetime.fromtimestamp(date / 1000)
        cursor.execute("""
            INSERT INTO trades (season_id, platform, traded_at, raw_details, is_partial)
            VALUES (%s, %s, %s, %s, TRUE)
            RETURNING trade_id;
        """, (season_id, "espn", traded_at, json.dumps(items)))
        trade_id = cursor.fetchone()[0]

        seen_owners = set()
        for item in items:
            if item["owner_id"] and item["owner_id"] not in seen_owners:
                cursor.execute("""
                    INSERT INTO trade_participants (trade_id, owner_id)
                    VALUES (%s, %s);
                """, (trade_id, item["owner_id"]))
                seen_owners.add(item["owner_id"])

    print(f"  Found {len(groups)} distinct trade events (partial data)")

conn.commit()
print("Done loading partial ESPN trades.")

cursor.close()
conn.close()