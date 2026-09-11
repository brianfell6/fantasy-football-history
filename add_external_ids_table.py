import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS owner_external_ids (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES owners(owner_id),
    platform TEXT NOT NULL,
    external_id TEXT NOT NULL
);
""")

conn.commit()
print("owner_external_ids table created.")

cursor.close()
conn.close()