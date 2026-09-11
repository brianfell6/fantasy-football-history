import json
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

with open("data/raw/sleeper/players.json") as f:
    player_lookup = json.load(f)

def player_name(player_id):
    p = player_lookup.get(str(player_id))
    if p:
        return p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
    return f"Unknown Player ({player_id})"

def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'sleeper';")
sleeper_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}

cursor.execute("SELECT owner_id, display_name FROM owners;")
owner_names = {row[0]: row[1] for row in cursor.fetchall()}

cursor.execute("SELECT season_id, year FROM seasons WHERE platform = 'sleeper';")
sleeper_season_lookup = {year: season_id for season_id, year in cursor.fetchall()}

cursor.execute("DELETE FROM trade_participants WHERE trade_id IN (SELECT trade_id FROM trades WHERE platform = 'sleeper');")
cursor.execute("DELETE FROM trades WHERE platform = 'sleeper';")
print("Cleared old Sleeper trades.")

years = ["2023", "2024", "2025", "2026"]

draft_data_by_year = {}
for year in years:
    slots_path = f"data/raw/sleeper/{year}_draft_info.json"
    picks_path = f"data/raw/sleeper/{year}_draft_picks.json"
    if os.path.exists(slots_path) and os.path.exists(picks_path):
        with open(slots_path) as f:
            draft_info = json.load(f)
        with open(picks_path) as f:
            draft_picks = json.load(f)
        slot_to_roster = {int(k): v for k, v in draft_info.get("slot_to_roster_id", {}).items()}
        roster_to_slot = {v: k for k, v in slot_to_roster.items()}
        draft_data_by_year[year] = {
            "roster_to_slot": roster_to_slot,
            "picks": draft_picks
        }

def resolve_pick_player(original_roster_id, round_num, pick_year):
    draft_data = draft_data_by_year.get(pick_year)
    if not draft_data:
        return None
    slot = draft_data["roster_to_slot"].get(original_roster_id)
    if slot is None:
        return None
    for pick in draft_data["picks"]:
        if pick.get("round") == round_num and pick.get("draft_slot") == slot:
            return player_name(pick.get("player_id"))
    return None

for year in years:
    print(f"Processing trades for {year}...")

    with open(f"data/raw/sleeper/{year}_rosters.json") as f:
        rosters = json.load(f)

    roster_to_owner = {}
    for roster in rosters:
        sleeper_user_id = roster.get("owner_id")
        owner_id = sleeper_id_to_owner.get(sleeper_user_id)
        if owner_id:
            roster_to_owner[roster["roster_id"]] = owner_id

    with open(f"data/raw/sleeper/{year}_trades.json") as f:
        trades = json.load(f)

    season_id = sleeper_season_lookup.get(int(year))

    for trade in trades:
        traded_at = datetime.fromtimestamp(trade["created"] / 1000)
        week = trade.get("leg")
        transaction_id = trade.get("transaction_id")

        adds = trade.get("adds") or {}
        picks = trade.get("draft_picks") or []
        all_roster_ids = trade.get("roster_ids", [])

        summary_by_owner = {}

        for roster_id in all_roster_ids:
            owner_id = roster_to_owner.get(roster_id)
            key = str(owner_id) if owner_id else f"roster_{roster_id}"
            summary_by_owner.setdefault(key, {"owner_name": owner_names.get(owner_id, f"Roster {roster_id}"), "players": [], "picks": []})

        for player_id, roster_id in adds.items():
            owner_id = roster_to_owner.get(roster_id)
            key = str(owner_id) if owner_id else f"roster_{roster_id}"
            summary_by_owner.setdefault(key, {"owner_name": owner_names.get(owner_id, f"Roster {roster_id}"), "players": [], "picks": []})
            summary_by_owner[key]["players"].append(player_name(player_id))

        for pick in picks:
            new_owner_roster_id = pick.get("owner_id")
            original_roster_id = pick.get("roster_id")
            pick_year = str(pick.get("season"))
            round_num = pick.get("round")

            owner_id = roster_to_owner.get(new_owner_roster_id)
            key = str(owner_id) if owner_id else f"roster_{new_owner_roster_id}"

            pick_desc = f"{pick_year} {ordinal(round_num)} Round Pick"
            became_player = resolve_pick_player(original_roster_id, round_num, pick_year)
            if became_player:
                pick_desc += f" ({became_player})"

            summary_by_owner.setdefault(key, {"owner_name": owner_names.get(owner_id, f"Roster {new_owner_roster_id}"), "players": [], "picks": []})
            summary_by_owner[key]["picks"].append(pick_desc)

        details = {"by_owner": summary_by_owner}

        cursor.execute("""
            INSERT INTO trades (season_id, platform, external_transaction_id, traded_at, week, raw_details)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING trade_id;
        """, (season_id, "sleeper", transaction_id, traded_at, week, json.dumps(details)))

        trade_id = cursor.fetchone()[0]

        for roster_id in all_roster_ids:
            owner_id = roster_to_owner.get(roster_id)
            if owner_id:
                cursor.execute("""
                    INSERT INTO trade_participants (trade_id, owner_id)
                    VALUES (%s, %s);
                """, (trade_id, owner_id))

    print(f"  Loaded {len(trades)} trades for {year}")

conn.commit()
print("Done loading Sleeper trades with player/pick/resolved-pick details.")

cursor.close()
conn.close()