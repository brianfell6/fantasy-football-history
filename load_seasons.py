import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

seasons_data = [
    (2017, "espn", "1334324"),
    (2018, "espn", "1334324"),
    (2019, "espn", "1334324"),
    (2021, "espn", "1334324"),
    (2022, "espn", "1334324"),
    (2023, "sleeper", "994110786538692608"),
    (2024, "sleeper", "1314327003792445440"),
    (2025, "sleeper", "1314327003792445440"),
    (2026, "sleeper", "1314327003792445440"),
]

for year, platform, league_id in seasons_data:
    cursor.execute(
        "INSERT INTO seasons (year, platform, league_id) VALUES (%s, %s, %s);",
        (year, platform, league_id)
    )
    print(f"Inserted {year} ({platform})")

conn.commit()
print("All seasons loaded.")

cursor.close()
conn.close()