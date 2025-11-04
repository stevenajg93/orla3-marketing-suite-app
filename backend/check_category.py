import psycopg2

DATABASE_URL = "postgresql://postgres:pcrmiSUNKiEyfEAIWKmfgfehGpKZzHmZ@switchyard.proxy.rlwy.net:34978/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=== BRAND_VOICE_ASSETS category constraint ===")
cur.execute("""
    SELECT constraint_name, check_clause
    FROM information_schema.check_constraints
    WHERE constraint_name LIKE '%brand_voice_assets_category%'
""")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n=== Categories in our JSON ===")
import json
with open("brand_voice_index.json") as f:
    data = json.load(f)
categories = set(asset.get("category") for asset in data.get("assets", []))
for cat in sorted(categories):
    print(f"  - {cat}")

cur.close()
conn.close()
