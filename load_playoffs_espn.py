import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'espn';")
espn_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}

cursor.execute("SELECT season_id, year FROM seasons WHERE platform = 'espn';")
espn_season_lookup = {year: season_id for season_id, year in cursor.fetchall()}

years = ["2017", "2018", "2019", "2021", "2022"]

for year in years:
    print(f"Processing ESPN playoffs for {year}...")

    with open(f"data/raw/espn/{year}.json") as f:
        raw = json.load(f)

    data = raw[0] if year == "2017" else raw

    playoff_team_count = data["settings"]["scheduleSettings"]["playoffTeamCount"]
    season_id = espn_season_lookup.get(int(year))

    for team in data.get("teams", []):
        owners = team.get("owners", [])
        if not owners:
            continue

        espn_member_id = owners[0].strip("{}")
        owner_id = espn_id_to_owner.get(espn_member_id)
        if not owner_id:
            print(f"  No owner match for {espn_member_id}, skipping")
            continue

        final_rank = team.get("rankCalculatedFinal", 0)
        made_playoffs = final_rank <= playoff_team_count and final_rank > 0
        won_championship = (final_rank == 1)

        cursor.execute("""
            UPDATE team_seasons
            SET made_playoffs = %s, won_championship = %s, final_standing = %s
            WHERE season_id = %s AND owner_id = %s;
        """, (made_playoffs, won_championship, final_rank, season_id, owner_id))

    print(f"  Loaded {year} (playoff cutoff: top {playoff_team_count})")

conn.commit()
print("Done loading ESPN playoffs.")

cursor.close()
conn.close()