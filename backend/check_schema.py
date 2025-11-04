import psycopg2

DATABASE_URL = "postgresql://postgres:pcrmiSUNKiEyfEAIWKmfgfehGpKZzHmZ@switchyard.proxy.rlwy.net:34978/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=== BRAND_VOICE_ASSETS COLUMNS ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'brand_voice_assets'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== CONTENT_CALENDAR COLUMNS ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'content_calendar'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== COMPETITORS COLUMNS ===")
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'competitors'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

cur.close()
conn.close()
