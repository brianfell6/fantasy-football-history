import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("""
    SELECT s.year, o.display_name, ts.team_name, ts.wins, ts.losses
    FROM team_seasons ts
    JOIN owners o ON ts.owner_id = o.owner_id
    JOIN seasons s ON ts.season_id = s.season_id
    WHERE ts.won_championship = TRUE
    ORDER BY s.year;
""")

print("=== CHAMPIONS ===")
for row in cursor.fetchall():
    print(row)

cursor.execute("""
    SELECT o.display_name,
           COUNT(*) FILTER (WHERE ts.won_championship = TRUE) AS championships,
           COUNT(*) FILTER (WHERE ts.made_playoffs = TRUE) AS playoff_appearances
    FROM team_seasons ts
    JOIN owners o ON ts.owner_id = o.owner_id
    GROUP BY o.display_name
    HAVING COUNT(*) FILTER (WHERE ts.made_playoffs = TRUE) > 0
    ORDER BY championships DESC, playoff_appearances DESC;
""")

print("\n=== PLAYOFF/CHAMPIONSHIP SUMMARY ===")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()