import json
import psycopg2
from datetime import datetime
from psycopg2.extras import Json
import os

DATABASE_URL = "postgresql://postgres:pcrmiSUNKiEyfEAIWKmfgfehGpKZzHmZ@switchyard.proxy.rlwy.net:34978/railway"

def migrate_brand_strategy():
    try:
        with open("brand_strategy.json") as f:
            strategy = json.load(f)
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO brand_strategy (brand_voice, messaging_pillars, language_patterns, dos_and_donts, target_audience, content_themes, competitive_positioning)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            Json(strategy.get("brand_voice",{})),
            strategy.get("messaging_pillars",[]),
            Json(strategy.get("language_patterns",{})),
            Json(strategy.get("dos_and_donts",{})),
            Json(strategy.get("target_audience",{})),
            strategy.get("content_themes",[]),
            Json(strategy.get("competitive_positioning",{}))
        ))
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Migrated brand_strategy (1 record)")
        return True
    except Exception as e:
        print(f"❌ brand_strategy: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_brand_voice_assets():
    try:
        with open("brand_voice_index.json") as f:
            data = json.load(f)
        assets = data.get("assets", [])
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        for asset in assets:
            try:
                uploaded_at = datetime.fromisoformat(asset.get("uploaded_at","").replace("Z","+00:00"))
            except:
                uploaded_at = datetime.now()
            
            filename = asset.get("filename", "")
            file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
            if not file_ext:
                file_ext = "unknown"
            
            category = asset.get("category")
            if category == "logos":
                category = "guidelines"
            
            metadata = {
                "source": asset.get("source"),
                "drive_file_id": asset.get("drive_file_id"),
                "drive_target_id": asset.get("drive_target_id"),
                "full_text": asset.get("full_text", ""),
                "original_category": asset.get("category")
            }
            
            cur.execute("""
                INSERT INTO brand_voice_assets (filename, category, file_type, file_path, file_size_bytes, content_preview, uploaded_at, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                filename,
                category,
                file_ext,
                asset.get("path"),
                asset.get("size"),
                asset.get("text_preview"),
                uploaded_at,
                Json(metadata)
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Migrated {len(assets)} brand voice assets")
        return True
    except Exception as e:
        print(f"❌ brand_voice_assets: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_content():
    try:
        with open("content_library.json") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get("content", [])
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        for item in items:
            try:
                created_at = datetime.fromisoformat(item.get("created_at","").replace("Z","+00:00"))
            except:
                created_at = datetime.now()
            
            cur.execute("""
                INSERT INTO content_library (title, content_type, content, status, platform, tags, media_url, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                item.get("title","Untitled"),
                item.get("content_type","blog"),
                item.get("content",""),
                item.get("status","draft"),
                item.get("platform"),
                item.get("tags",[]),
                item.get("media_url"),
                created_at
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Migrated {len(items)} content items")
        return True
    except Exception as e:
        print(f"❌ content: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_calendar():
    try:
        with open("calendar_data.json") as f:
            events = json.load(f)
        if not isinstance(events, list):
            events = []
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        for event in events:
            try:
                scheduled_date = datetime.fromisoformat(event.get("scheduled_date","").replace("Z","+00:00"))
            except:
                continue
            
            status = event.get("status", "draft")
            if status == "draft":
                status = "scheduled"
            
            notes_content = event.get("content", "")
            if event.get("media_url"):
                notes_content += f"\nMedia: {event.get('media_url')}"
            
            cur.execute("""
                INSERT INTO content_calendar (title, content_type, scheduled_date, status, platform, notes)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                event.get("title","Untitled"),
                event.get("content_type","text"),
                scheduled_date,
                status,
                event.get("platform"),
                notes_content
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Migrated {len(events)} calendar events")
        return True
    except Exception as e:
        print(f"❌ calendar: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_competitors():
    try:
        with open("competitor_data.json") as f:
            data = json.load(f)
        competitors = data.get("competitors", [])
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        for comp in competitors:
            try:
                last_analyzed = datetime.fromisoformat(comp.get("last_analyzed","").replace("Z","+00:00"))
            except:
                last_analyzed = None
            try:
                added_at = datetime.fromisoformat(comp.get("added_at","").replace("Z","+00:00"))
            except:
                added_at = datetime.now()
            
            cur.execute("""
                INSERT INTO competitors (name, industry, location, social_handles, last_analyzed, added_at)
                VALUES (%s,%s,%s,%s,%s,%s) RETURNING id
            """, (
                comp.get("name"),
                comp.get("industry"),
                comp.get("location"),
                Json(comp.get("handles",{})),
                last_analyzed,
                added_at
            ))
            comp_id = cur.fetchone()[0]
            
            analysis = comp.get("analysis")
            if analysis:
                cur.execute("""
                    INSERT INTO competitor_analyses (
                        competitor_id, marketing_they_do_well, gaps_they_miss,
                        positioning_messaging, content_opportunities,
                        threat_level, strategic_summary, raw_analysis
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    comp_id,
                    analysis.get("marketing_they_do_well",[]),
                    analysis.get("content_gaps",[]),
                    analysis.get("positioning_messaging"),
                    analysis.get("content_opportunities",[]),
                    analysis.get("threat_level","medium"),
                    analysis.get("strategic_summary"),
                    Json(analysis)
                ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Migrated {len(competitors)} competitors with analyses")
        return True
    except Exception as e:
        print(f"❌ competitors: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting ONE Clean Migration to PostgreSQL...")
    print()
    success_count = 0
    
    if migrate_brand_strategy(): success_count += 1
    if migrate_brand_voice_assets(): success_count += 1
    if migrate_content(): success_count += 1
    if migrate_calendar(): success_count += 1
    if migrate_competitors(): success_count += 1
    
    print()
    print(f"{'✅' if success_count == 5 else '⚠️'} Migration complete: {success_count}/5 successful")
