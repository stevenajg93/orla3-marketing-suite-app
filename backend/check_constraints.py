import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=== BRAND_VOICE_ASSETS file_type column ===")
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name = 'brand_voice_assets' AND column_name = 'file_type'
""")
print(cur.fetchone())

print("\n=== CONTENT_CALENDAR status constraint ===")
cur.execute("""
    SELECT constraint_name, check_clause
    FROM information_schema.check_constraints
    WHERE constraint_name LIKE '%content_calendar_status%'
""")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

cur.close()
conn.close()
