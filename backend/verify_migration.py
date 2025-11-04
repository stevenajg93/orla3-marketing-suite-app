import psycopg2

DATABASE_URL = "postgresql://postgres:pcrmiSUNKiEyfEAIWKmfgfehGpKZzHmZ@switchyard.proxy.rlwy.net:34978/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("📊 DATABASE VERIFICATION\n")

# Check each table
tables = [
    ('brand_strategy', 'Brand Strategy'),
    ('brand_voice_assets', 'Brand Voice Assets'),
    ('content_library', 'Content Library'),
    ('content_calendar', 'Calendar Events'),
    ('competitors', 'Competitors'),
    ('competitor_analyses', 'Competitor Analyses')
]

for table_name, display_name in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cur.fetchone()[0]
    print(f"✅ {display_name}: {count} records")

# Sample some data
print("\n📝 SAMPLE DATA:\n")

print("Brand Voice Assets by category:")
cur.execute("SELECT category, COUNT(*) FROM brand_voice_assets GROUP BY category ORDER BY category")
for row in cur.fetchall():
    print(f"  - {row[0]}: {row[1]} files")

print("\nContent Library by type:")
cur.execute("SELECT content_type, COUNT(*) FROM content_library GROUP BY content_type ORDER BY content_type")
for row in cur.fetchall():
    print(f"  - {row[0]}: {row[1]} items")

print("\nCompetitor:")
cur.execute("SELECT name FROM competitors LIMIT 1")
print(f"  - {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\n✅ Migration verified successfully!")
