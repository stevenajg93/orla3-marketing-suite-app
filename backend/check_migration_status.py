#!/usr/bin/env python3
import os
import psycopg2

# Read DATABASE_URL from .env file
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('DATABASE_URL'):
            DATABASE_URL = line.split('=', 1)[1].strip()
            break
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Check what tables exist
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = cur.fetchall()

print("\n📋 EXISTING TABLES:")
print("=" * 50)
for t in tables:
    print(f"  ✓ {t[0]}")

# Check if user_id columns exist
print("\n🔍 CHECKING user_id COLUMNS:")
print("=" * 50)
for table in ['brand_strategy', 'brand_voice_assets', 'competitors', 'content_library', 'content_calendar', 'published_posts']:
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = '{table}' AND column_name = 'user_id'
    """)
    exists = cur.fetchone()
    status = "✓ EXISTS" if exists else "✗ MISSING"
    print(f"  {table}: {status}")

cur.close()
conn.close()
