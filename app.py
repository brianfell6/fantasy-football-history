from flask import Flask, render_template
import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(os.environ["SUPABASE_DB_URL"])

with open("data/raw/sleeper/players.json") as f:
    SLEEPER_PLAYERS = json.load(f)

def sleeper_player_name(player_id):
    p = SLEEPER_PLAYERS.get(str(player_id))
    if p:
        return p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
    return f"Unknown Player ({player_id})"

with open("data/raw/espn/players.json") as f:
    ESPN_PLAYERS = json.load(f)

def espn_player_name(player_id, fallback_lookup=None):
    if fallback_lookup and player_id in fallback_lookup:
        return fallback_lookup[player_id]
    name = ESPN_PLAYERS.get(str(player_id))
    if name:
        return name
    return f"Unknown Player ({player_id})"

@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.owner_id, o.display_name,
               COUNT(*) AS seasons_played,
               SUM(ts.wins) AS total_wins,
               SUM(ts.losses) AS total_losses,
               COUNT(*) FILTER (WHERE ts.won_championship = TRUE) AS championships
        FROM team_seasons ts
        JOIN owners o ON ts.owner_id = o.owner_id
        GROUP BY o.owner_id, o.display_name
        ORDER BY championships DESC, total_wins DESC;
    """)
    leaderboard = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("home.html", leaderboard=leaderboard)

@app.route("/owner/<int:owner_id>")
def owner_detail(owner_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT display_name FROM owners WHERE owner_id = %s;", (owner_id,))
    owner_name = cursor.fetchone()[0]

    cursor.execute("""
        SELECT s.year, s.platform, ts.team_name, ts.wins, ts.losses, ts.points_for,
               ts.made_playoffs, ts.won_championship
        FROM team_seasons ts
        JOIN seasons s ON ts.season_id = s.season_id
        WHERE ts.owner_id = %s
        ORDER BY s.year;
    """, (owner_id,))
    seasons = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("owner.html", owner_name=owner_name, seasons=seasons)

@app.route("/champions")
def champions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.year, s.platform, o.owner_id, o.display_name, ts.team_name, ts.wins, ts.losses
        FROM team_seasons ts
        JOIN owners o ON ts.owner_id = o.owner_id
        JOIN seasons s ON ts.season_id = s.season_id
        WHERE ts.won_championship = TRUE
        ORDER BY s.year;
    """)
    champs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("champions.html", champs=champs)

@app.route("/seasons")
def seasons_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT season_id, year, platform
        FROM seasons
        ORDER BY year DESC;
    """)
    all_seasons = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("seasons_list.html", all_seasons=all_seasons)

def get_sleeper_bracket_matches(year, roster_to_owner):
    bracket_path = f"data/raw/sleeper/{year}_bracket.json"
    if not os.path.exists(bracket_path):
        return None

    with open(bracket_path) as f:
        bracket = json.load(f)

    matches = []
    for match in bracket:
        t1_owner = roster_to_owner.get(match.get("t1"))
        t2_owner = roster_to_owner.get(match.get("t2"))
        winner_owner = roster_to_owner.get(match.get("w"))
        matches.append({
            "round": match.get("r"),
            "team1": t1_owner,
            "team2": t2_owner,
            "winner": winner_owner,
            "is_championship": match.get("p") == 1
        })
    return matches

@app.route("/season/<int:season_id>")
def season_detail(season_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT year, platform FROM seasons WHERE season_id = %s;", (season_id,))
    year, platform = cursor.fetchone()

    cursor.execute("""
        SELECT o.owner_id, o.display_name, ts.team_name, ts.wins, ts.losses,
               ts.points_for, ts.points_against, ts.made_playoffs, ts.won_championship
        FROM team_seasons ts
        JOIN owners o ON ts.owner_id = o.owner_id
        WHERE ts.season_id = %s
        ORDER BY ts.wins DESC, ts.points_for DESC;
    """, (season_id,))
    teams = cursor.fetchall()

    bracket_matches = None
    if platform == "sleeper":
        cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'sleeper';")
        sleeper_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}

        rosters_path = f"data/raw/sleeper/{year}_rosters.json"
        if os.path.exists(rosters_path):
            with open(rosters_path) as f:
                rosters = json.load(f)
            roster_to_owner = {}
            for roster in rosters:
                sleeper_user_id = roster.get("owner_id")
                owner_id = sleeper_id_to_owner.get(sleeper_user_id)
                if owner_id:
                    roster_to_owner[roster["roster_id"]] = owner_id

            owner_names = {row[0]: row[1] for row in teams}
            bracket_matches = get_sleeper_bracket_matches(year, roster_to_owner)
            if bracket_matches:
                for m in bracket_matches:
                    m["team1_name"] = owner_names.get(m["team1"], "TBD")
                    m["team2_name"] = owner_names.get(m["team2"], "TBD")
                    m["winner_name"] = owner_names.get(m["winner"], "TBD")

    cursor.close()
    conn.close()
    return render_template("season_detail.html", year=year, platform=platform, teams=teams, bracket_matches=bracket_matches, season_id=season_id)

def get_owner_team_names(season_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.owner_id, o.display_name, ts.team_name
        FROM team_seasons ts
        JOIN owners o ON ts.owner_id = o.owner_id
        WHERE ts.season_id = %s;
    """, (season_id,))
    result = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return result

@app.route("/season/<int:season_id>/rosters")
def season_rosters(season_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT year, platform FROM seasons WHERE season_id = %s;", (season_id,))
    year, platform = cursor.fetchone()
    cursor.close()
    conn.close()

    owner_team_names = get_owner_team_names(season_id)
    rosters_display = []

    if platform == "sleeper":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'sleeper';")
        sleeper_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}
        cursor.close()
        conn.close()

        with open(f"data/raw/sleeper/{year}_rosters.json") as f:
            rosters = json.load(f)

        for roster in rosters:
            sleeper_user_id = roster.get("owner_id")
            owner_id = sleeper_id_to_owner.get(sleeper_user_id)
            if not owner_id or owner_id not in owner_team_names:
                continue
            owner_name, team_name = owner_team_names[owner_id]
            player_ids = roster.get("players") or []
            player_names = sorted(sleeper_player_name(pid) for pid in player_ids)
            rosters_display.append({
                "owner_name": owner_name,
                "team_name": team_name,
                "players": player_names
            })

    elif platform == "espn":
        with open(f"data/raw/espn/{year}.json") as f:
            raw = json.load(f)
        data = raw[0] if year == 2017 else raw

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'espn';")
        espn_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}
        cursor.close()
        conn.close()

        for team in data.get("teams", []):
            owners = team.get("owners", [])
            if not owners:
                continue
            espn_member_id = owners[0].strip("{}")
            owner_id = espn_id_to_owner.get(espn_member_id)
            if not owner_id or owner_id not in owner_team_names:
                continue
            owner_name, team_name = owner_team_names[owner_id]
            player_names = sorted(
                entry["playerPoolEntry"]["player"]["fullName"]
                for entry in team.get("roster", {}).get("entries", [])
            )
            rosters_display.append({
                "owner_name": owner_name,
                "team_name": team_name,
                "players": player_names
            })

    return render_template("season_rosters.html", year=year, platform=platform, rosters=rosters_display, season_id=season_id, roster_type="Final")

@app.route("/season/<int:season_id>/draft")
def season_draft(season_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT year, platform FROM seasons WHERE season_id = %s;", (season_id,))
    year, platform = cursor.fetchone()
    cursor.close()
    conn.close()

    owner_team_names = get_owner_team_names(season_id)
    draft_by_owner = {}

    if platform == "sleeper":
        picks_path = f"data/raw/sleeper/{year}_draft_picks.json"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'sleeper';")
        sleeper_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}
        cursor.close()
        conn.close()

        if os.path.exists(picks_path):
            with open(picks_path) as f:
                draft_picks = json.load(f)

            for pick in sorted(draft_picks, key=lambda p: p.get("pick_no", 0)):
                sleeper_user_id = pick.get("picked_by")
                owner_id = sleeper_id_to_owner.get(sleeper_user_id)
                if not owner_id or owner_id not in owner_team_names:
                    continue
                owner_name, team_name = owner_team_names[owner_id]
                player_name = sleeper_player_name(pick.get("player_id"))
                round_num = pick.get("round")
                pick_no = pick.get("pick_no")

                draft_by_owner.setdefault(owner_id, {"owner_name": owner_name, "team_name": team_name, "picks": []})
                draft_by_owner[owner_id]["picks"].append({"round": round_num, "pick_no": pick_no, "player": player_name})

    elif platform == "espn":
        with open(f"data/raw/espn/{year}.json") as f:
            raw = json.load(f)
        data = raw[0] if year == 2017 else raw

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT owner_id, external_id FROM owner_external_ids WHERE platform = 'espn';")
        espn_id_to_owner = {ext_id: owner_id for owner_id, ext_id in cursor.fetchall()}
        cursor.close()
        conn.close()

        # Build teamId -> owner_id using each team's real owners list (reliable across all years)
        team_id_to_owner = {}
        roster_name_lookup = {}
        for team in data.get("teams", []):
            owners = team.get("owners", [])
            if owners:
                espn_member_id = owners[0].strip("{}")
                owner_id = espn_id_to_owner.get(espn_member_id)
                if owner_id:
                    team_id_to_owner[team.get("id")] = owner_id
            for entry in team.get("roster", {}).get("entries", []):
                player = entry["playerPoolEntry"]["player"]
                roster_name_lookup[player["id"]] = player["fullName"]

        draft_picks = data.get("draftDetail", {}).get("picks", [])
        for pick in sorted(draft_picks, key=lambda p: p.get("overallPickNumber", 0)):
            team_id = pick.get("teamId")
            owner_id = team_id_to_owner.get(team_id)
            if not owner_id or owner_id not in owner_team_names:
                continue
            owner_name, team_name = owner_team_names[owner_id]
            player_name = espn_player_name(pick.get("playerId"), roster_name_lookup)
            round_num = pick.get("roundId")
            pick_no = pick.get("overallPickNumber")

            draft_by_owner.setdefault(owner_id, {"owner_name": owner_name, "team_name": team_name, "picks": []})
            draft_by_owner[owner_id]["picks"].append({"round": round_num, "pick_no": pick_no, "player": player_name})

    rosters_display = list(draft_by_owner.values())
    return render_template("season_draft.html", year=year, platform=platform, rosters=rosters_display, season_id=season_id)

@app.route("/trades")
def trades_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT owner_id, display_name FROM owners;")
    owner_names = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT t.trade_id, s.year, s.platform, t.traded_at, t.is_partial, t.raw_details
        FROM trades t
        JOIN seasons s ON t.season_id = s.season_id
        ORDER BY t.traded_at DESC;
    """)
    raw_trades = cursor.fetchall()
    cursor.close()
    conn.close()

    all_trades = []
    for trade_id, year, platform, traded_at, is_partial, raw_details in raw_trades:
        sides = []

        if platform == "sleeper" and raw_details and "by_owner" in raw_details:
            for entry in raw_details["by_owner"].values():
                sides.append({
                    "owner_name": entry.get("owner_name", "Unknown"),
                    "players": entry.get("players", []),
                    "picks": entry.get("picks", [])
                })
        elif platform == "espn" and raw_details:
            grouped = {}
            for item in raw_details:
                owner_id = item.get("owner_id")
                name = owner_names.get(owner_id, "Unknown")
                grouped.setdefault(name, []).append(item.get("player"))
            for name, players in grouped.items():
                sides.append({"owner_name": name, "players": players, "picks": []})

        all_trades.append({
            "trade_id": trade_id,
            "year": year,
            "platform": platform,
            "traded_at": traded_at,
            "is_partial": is_partial,
            "sides": sides
        })

    return render_template("trades.html", all_trades=all_trades)

if __name__ == "__main__":
    app.run(debug=True)