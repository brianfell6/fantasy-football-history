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
for s_id, platform, year in cursor.fetchall():
    season_lookup[(platform, year)] = s_id

years = ["2017", "2018", "2019", "2021", "2022"]

for year in years:
    print(f"Processing ESPN {year}...")

    with open(f"data/raw/espn/{year}.json") as f:
        raw = json.load(f)

    data = raw[0] if year == "2017" else raw

    season_id = season_lookup.get(("espn", int(year)))
    if not season_id:
        print(f"  No season found for {year}, skipping")
        continue

    teams = data.get("teams", [])

    for team in teams:
        owners = team.get("owners", [])
        if not owners:
            print(f"  Team {team.get('id')} has no owners listed, skipping")
            continue

        # Some teams list multiple owners (co-managed); we use the first as primary
        espn_member_id = owners[0].strip("{}")
        owner_id = owner_lookup.get(("espn", espn_member_id))
        if not owner_id:
            print(f"  No owner match for espn_member_id {espn_member_id}, skipping")
            continue

        record = team.get("record", {}).get("overall", {})
        wins = record.get("wins", 0)
        losses = record.get("losses", 0)
        ties = record.get("ties", 0)
        points_for = record.get("pointsFor", 0)
        points_against = record.get("pointsAgainst", 0)

        location = team.get("location", "")
        nickname = team.get("nickname", "")
        team_name = f"{location} {nickname}".strip() or team.get("name", "Unknown")

        cursor.execute("""
            INSERT INTO team_seasons
            (season_id, owner_id, team_name, wins, losses, ties, points_for, points_against)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (season_id, owner_id, team_name, wins, losses, ties, points_for, points_against))

    print(f"  Loaded {year}")

conn.commit()
print("Done loading ESPN team_seasons.")

cursor.close()
conn.close()