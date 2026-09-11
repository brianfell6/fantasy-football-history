import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("""
    SELECT t.trade_id, s.year, t.traded_at, string_agg(o.display_name, ' <-> ')
    FROM trades t
    JOIN seasons s ON t.season_id = s.season_id
    JOIN trade_participants tp ON t.trade_id = tp.trade_id
    JOIN owners o ON tp.owner_id = o.owner_id
    GROUP BY t.trade_id, s.year, t.traded_at
    ORDER BY t.traded_at
    LIMIT 10;
""")

for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()