import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("""
    SELECT o.display_name,
           COUNT(*) AS seasons_played,
           SUM(ts.wins) AS total_wins,
           SUM(ts.losses) AS total_losses,
           ROUND(SUM(ts.wins)::numeric / NULLIF(SUM(ts.wins) + SUM(ts.losses), 0), 3) AS win_pct,
           ROUND(SUM(ts.points_for)::numeric, 1) AS total_points_for
    FROM team_seasons ts
    JOIN owners o ON ts.owner_id = o.owner_id
    GROUP BY o.display_name
    ORDER BY win_pct DESC;
""")

print(f"{'Owner':<30} {'Seasons':<10} {'W':<6} {'L':<6} {'Win%':<8} {'Total PF':<12}")
for row in cursor.fetchall():
    name, seasons, wins, losses, win_pct, pf = row
    win_pct_display = f"{win_pct}" if win_pct is not None else "N/A"
    pf_display = f"{pf}" if pf is not None else "0.0"
    print(f"{name:<30} {seasons:<10} {wins:<6} {losses:<6} {win_pct_display:<8} {pf_display:<12}")

cursor.close()
conn.close()