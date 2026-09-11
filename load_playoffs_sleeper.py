import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'sleeper';")
sleeper_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}

cursor.execute("SELECT season_id, year FROM seasons WHERE platform = 'sleeper';")
sleeper_season_lookup = {year: season_id for season_id, year in cursor.fetchall()}

years = ["2023", "2024", "2025"]

for year in years:
    print(f"Processing playoffs for {year}...")

    with open(f"data/raw/sleeper/{year}_rosters.json") as f:
        rosters = json.load(f)

    roster_to_owner = {}
    for roster in rosters:
        sleeper_user_id = roster.get("owner_id")
        owner_id = sleeper_id_to_owner.get(sleeper_user_id)
        if owner_id:
            roster_to_owner[roster["roster_id"]] = owner_id

    with open(f"data/raw/sleeper/{year}_bracket.json") as f:
        bracket = json.load(f)

    playoff_roster_ids = set()
    champion_roster_id = None

    for match in bracket:
        if match.get("r") == 1:
            playoff_roster_ids.add(match["t1"])
            playoff_roster_ids.add(match["t2"])
        if match.get("p") == 1:
            champion_roster_id = match["w"]

    season_id = sleeper_season_lookup.get(int(year))

    for roster_id in playoff_roster_ids:
        owner_id = roster_to_owner.get(roster_id)
        if not owner_id:
            continue
        won_it_all = (roster_id == champion_roster_id)
        cursor.execute("""
            UPDATE team_seasons
            SET made_playoffs = TRUE, won_championship = %s
            WHERE season_id = %s AND owner_id = %s;
        """, (won_it_all, season_id, owner_id))

    print(f"  {len(playoff_roster_ids)} playoff teams, champion owner_id: {roster_to_owner.get(champion_roster_id)}")

conn.commit()
print("Done loading Sleeper playoffs.")

cursor.close()
conn.close()