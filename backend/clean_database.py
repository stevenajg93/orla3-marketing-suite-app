import psycopg2

DATABASE_URL = "postgresql://postgres:pcrmiSUNKiEyfEAIWKmfgfehGpKZzHmZ@switchyard.proxy.rlwy.net:34978/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("🧹 Cleaning database...")
cur.execute("TRUNCATE brand_strategy, brand_voice_assets, content_library, content_calendar, competitor_analyses, competitors, published_posts CASCADE")
conn.commit()
cur.close()
conn.close()
print("✅ Database wiped clean - ready for ONE clean migration")
