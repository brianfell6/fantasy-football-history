import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

# Build a lookup: (platform, external_id) -> owner_id
cursor.execute("SELECT owner_id, platform, external_id FROM owner_external_ids;")
owner_lookup = {}
for owner_id, platform, external_id in cursor.fetchall():
    owner_lookup[(platform, external_id)] = owner_id

# Build a lookup: (platform, year) -> season_id
cursor.execute("SELECT season_id, platform, year FROM seasons;")
season_lookup = {}
for season_id, platform, year in cursor.fetchall():
    season_lookup[(platform, year)] = season_id

years = ["2023", "2024", "2025", "2026"]

for year in years:
    print(f"Processing Sleeper {year}...")

    with open(f"data/raw/sleeper/{year}_users.json") as f:
        users = json.load(f)

    with open(f"data/raw/sleeper/{year}_rosters.json") as f:
        rosters = json.load(f)

    # Map user_id -> team name (falls back to display_name if no custom team name set)
    team_names = {}
    for user in users:
        name = user.get("metadata", {}).get("team_name") or user["display_name"]
        team_names[user["user_id"]] = name

    season_id = season_lookup.get(("sleeper", int(year)))
    if not season_id:
        print(f"  No season found for {year}, skipping")
        continue

    for roster in rosters:
        sleeper_user_id = roster.get("owner_id")
        if not sleeper_user_id:
            print(f"  Roster with no owner_id, skipping")
            continue

        owner_id = owner_lookup.get(("sleeper", sleeper_user_id))
        if not owner_id:
            print(f"  No owner match for sleeper_user_id {sleeper_user_id}, skipping")
            continue

        settings = roster.get("settings", {})
        wins = settings.get("wins", 0)
        losses = settings.get("losses", 0)
        ties = settings.get("ties", 0)
        points_for = settings.get("fpts", 0) + settings.get("fpts_decimal", 0) / 100
        points_against = settings.get("fpts_against", 0) + settings.get("fpts_against_decimal", 0) / 100
        team_name = team_names.get(sleeper_user_id, "Unknown")

        cursor.execute("""
            INSERT INTO team_seasons
            (season_id, owner_id, team_name, wins, losses, ties, points_for, points_against)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (season_id, owner_id, team_name, wins, losses, ties, points_for, points_against))

    print(f"  Loaded {year}")

conn.commit()
print("Done loading Sleeper team_seasons.")

cursor.close()
conn.close()