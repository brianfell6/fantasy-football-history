import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    trade_id SERIAL PRIMARY KEY,
    season_id INTEGER REFERENCES seasons(season_id),
    platform TEXT NOT NULL,
    external_transaction_id TEXT,
    traded_at TIMESTAMP,
    week INTEGER,
    raw_details JSONB
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS trade_participants (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(trade_id),
    owner_id INTEGER REFERENCES owners(owner_id)
);
""")

conn.commit()
print("Trade tables created.")

cursor.close()
conn.close()