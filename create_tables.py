import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS owners (
    owner_id SERIAL PRIMARY KEY,
    display_name TEXT NOT NULL,
    sleeper_user_id TEXT,
    espn_owner_id TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS seasons (
    season_id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    platform TEXT NOT NULL,
    league_id TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS team_seasons (
    team_season_id SERIAL PRIMARY KEY,
    season_id INTEGER REFERENCES seasons(season_id),
    owner_id INTEGER REFERENCES owners(owner_id),
    team_name TEXT,
    wins INTEGER,
    losses INTEGER,
    ties INTEGER,
    points_for NUMERIC,
    points_against NUMERIC,
    final_standing INTEGER,
    made_playoffs BOOLEAN,
    won_championship BOOLEAN
);
""")

conn.commit()
print("Tables created successfully!")

cursor.close()
conn.close()