from fastapi import APIRouter, HTTPException, Request
from anthropic import Anthropic
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json as PgJson
from datetime import datetime
from pathlib import Path
from openai import OpenAI
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import decode_token
from utils.credits import deduct_credits, InsufficientCreditsError

router = APIRouter()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_user_from_token(request: Request):
    """Extract user_id from JWT token"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get('sub')  # user_id

def load_brand_voice_assets(user_id: str):
    """Load all uploaded brand voice assets from PostgreSQL for a specific user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM brand_voice_assets WHERE user_id = %s ORDER BY uploaded_at DESC", (user_id,))
        assets = cur.fetchall()
        cur.close()
        conn.close()
        return assets
    except Exception as e:
        print(f"Error loading brand voice assets: {e}")
        return []

def load_competitor_summary(user_id: str):
    """Load competitor marketing insights summary from PostgreSQL for a specific user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all competitors with their analyses for this user
        cur.execute("""
            SELECT c.*, ca.*
            FROM competitors c
            LEFT JOIN competitor_analyses ca ON c.id = ca.competitor_id
            WHERE c.user_id = %s
            ORDER BY c.added_at DESC
        """, (user_id,))
        competitors = cur.fetchall()
        cur.close()
        conn.close()
        
        if not competitors:
            return None
        
        # Build summary
        analyzed = [c for c in competitors if c.get('marketing_they_do_well')]
        
        if not analyzed:
            return None
        
        summary = {
            'total': len(competitors),
            'analyzed': len(analyzed),
            'competitors': []
        }
        
        for comp in analyzed:
            summary['competitors'].append({
                'name': comp['name'],
                'threat_level': comp.get('threat_level', 'unknown'),
                'marketing_they_do_well': comp.get('marketing_they_do_well', []),
                'content_gaps': comp.get('gaps_they_miss', []),  # Database uses gaps_they_miss
                'positioning_messaging': comp.get('positioning_messaging', ''),
                'content_opportunities': comp.get('content_opportunities', [])
            })
        
        return summary
        
    except Exception as e:
        print(f"Error loading competitor summary: {e}")
        return None

def load_brand_strategy(user_id: str):
    """Load brand strategy from PostgreSQL for a specific user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM brand_strategy WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
        strategy = cur.fetchone()
        cur.close()
        conn.close()
        return dict(strategy) if strategy else None
    except Exception as e:
        print(f"Error loading brand strategy: {e}")
        return None

def extract_text_from_file(file_path: str) -> str:
    """Extract text from various file formats"""
    file_ext = Path(file_path).suffix.lower()
    
    try:
        # TXT files
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # DOCX files
        elif file_ext == '.docx':
            try:
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            except Exception as e:
                return f"Could not extract DOCX text: {str(e)}"
        
        # PDF files
        elif file_ext == '.pdf':
            try:
                import PyPDF2
                text = []
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages:
                        text.append(page.extract_text())
                return '\n'.join(text)
            except Exception as e:
                return f"Could not extract PDF text: {str(e)}"
        
        # Excel files (Discord exports)
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            try:
                import pandas as pd
                if file_ext == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                return df.to_string()
            except Exception as e:
                return f"Could not extract spreadsheet text: {str(e)}"
        
        else:
            return f"Unsupported file type: {file_ext}"
            
    except Exception as e:
        return f"Error reading file: {str(e)}"

@router.post("/analyze")
async def analyze_brand_voice(request: Request, include_competitors: bool = True):
    """
    Analyze brand voice assets and optionally include competitive MARKETING intelligence
    """
    try:
        user_id = get_user_from_token(request)

        # Check and deduct credits BEFORE generating strategy (10 credits)
        try:
            deduct_credits(
                user_id=user_id,
                operation_type="strategy_generation",
                operation_details={
                    "include_competitors": include_competitors
                },
                description="Generated brand strategy and marketing intelligence"
            )
        except InsufficientCreditsError as e:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": f"Insufficient credits. Required: {e.required}, Available: {e.available}",
                    "required": e.required,
                    "available": e.available
                }
            )

        # Load assets from PostgreSQL for this user
        assets = load_brand_voice_assets(user_id)
        
        if not assets:
            return {
                "success": False,
                "error": "No brand voice assets uploaded yet. Please upload training materials first."
            }
        
        # Extract text from files and organize by category
        brand_context = {
            "guidelines": [],
            "voice_samples": [],
            "target_audience_insights": []
        }

        print(f"Processing {len(assets)} assets...")

        for asset in assets:
            # Get text from metadata or content_preview
            text = ""
            if asset.get('metadata') and isinstance(asset['metadata'], dict):
                text = asset['metadata'].get('full_text', '')
            if not text:
                text = asset.get('content_preview', '')

            # Try to extract if not available
            if not text or text == "No text extracted":
                print(f"Extracting text from {asset['filename']}...")
                text = extract_text_from_file(asset['file_path'])

            # Skip if no text extracted
            if not text or len(text) < 50:
                print(f"Skipping {asset['filename']} - insufficient text")
                continue

            # Categorize
            category = asset['category']
            if category == 'guidelines':
                brand_context['guidelines'].append({
                    'filename': asset['filename'],
                    'text': text[:3000]
                })
            elif category == 'voice_samples':
                brand_context['voice_samples'].append({
                    'filename': asset['filename'],
                    'text': text[:2000]
                })
            elif category == 'target_audience_insights':
                brand_context['target_audience_insights'].append({
                    'filename': asset['filename'],
                    'text': text[:1500]
                })
            # Support legacy categories for backwards compatibility
            elif category in ['community_videographer', 'community_client']:
                brand_context['target_audience_insights'].append({
                    'filename': asset['filename'],
                    'text': text[:1500]
                })

        print(f"Context prepared: {len(brand_context['guidelines'])} guidelines, {len(brand_context['voice_samples'])} samples, {len(brand_context['target_audience_insights'])} audience insights")
        
        # Load competitor MARKETING insights if requested
        competitor_context = ""
        competitor_summary = None

        if include_competitors:
            competitor_summary = load_competitor_summary(user_id)
            if competitor_summary and competitor_summary['analyzed'] > 0:
                competitor_context = f"""

COMPETITIVE MARKETING INTELLIGENCE ({competitor_summary['analyzed']} competitors analyzed):

"""
                for comp in competitor_summary['competitors']:
                    competitor_context += f"""
**{comp['name']}** (Marketing Threat: {comp['threat_level']})
- Marketing/Content they do well: {', '.join(comp['marketing_they_do_well'][:3]) if comp['marketing_they_do_well'] else 'N/A'}
- Content gaps they miss: {', '.join(comp['content_gaps'][:2]) if comp['content_gaps'] else 'N/A'}
- Our messaging positioning: {comp['positioning_messaging'][:200] if comp['positioning_messaging'] else 'N/A'}
"""
                
                competitor_context += """
MARKETING STRATEGY DIRECTIVE:
- Adapt competitor CONTENT/MESSAGING strategies that work (in our authentic voice)
- Exploit CONTENT GAPS they're missing
- Position our MESSAGING clearly against them while staying true to our brand

CRITICAL: Use competitive insights ONLY for CONTENT & MARKETING strategy, NOT product development.
"""
        
        # Build analysis prompt
        brand_files_context = f"""
**BRAND GUIDELINES ({len(brand_context['guidelines'])} files):**
{chr(10).join([f"- {item['filename']}: {item['text'][:500]}..." for item in brand_context['guidelines']]) if brand_context['guidelines'] else "None uploaded"}

**VOICE SAMPLES ({len(brand_context['voice_samples'])} files):**
{chr(10).join([f"- {item['filename']}: {item['text'][:500]}..." for item in brand_context['voice_samples']]) if brand_context['voice_samples'] else "None uploaded"}

**TARGET AUDIENCE INSIGHTS ({len(brand_context['target_audience_insights'])} files):**
{chr(10).join([f"- {item['filename']}: {item['text'][:300]}..." for item in brand_context['target_audience_insights']]) if brand_context['target_audience_insights'] else "None uploaded"}
"""

        prompt = f"""You are a CONTENT MARKETING strategist creating a comprehensive CONTENT & MESSAGING strategy.

BRAND VOICE TRAINING MATERIALS:
{brand_files_context}
{competitor_context}

Analyze these materials and create a strategic brief that balances authentic brand voice with competitive MARKETING positioning.

CRITICAL: The competitive_positioning section should focus ONLY on CONTENT & MARKETING strategy:
- Content topics and themes
- Messaging and positioning
- Brand voice differentiation
- Marketing tactics

DO NOT include product features, business models, or operational recommendations.

Return ONLY valid JSON (no markdown) in this exact format:
{{
  "brand_voice": {{
    "tone": "description of tone",
    "personality": ["trait1", "trait2", "trait3"],
    "key_characteristics": ["characteristic1", "characteristic2"]
  }},
  "messaging_pillars": ["pillar1", "pillar2", "pillar3"],
  "language_patterns": {{
    "preferred_phrases": ["phrase1", "phrase2"],
    "vocabulary": ["word1", "word2"],
    "writing_style": "description"
  }},
  "dos_and_donts": {{
    "dos": ["do1", "do2"],
    "donts": ["dont1", "dont2"]
  }},
  "target_audience": {{
    "primary": "description",
    "characteristics": ["char1", "char2"]
  }},
  "content_themes": ["theme1", "theme2", "theme3"],
  "competitive_positioning": {{
    "unique_value": "What makes our MESSAGING/POSITIONING different",
    "copy_and_adapt": ["CONTENT/MESSAGING strategies competitors use that we should adapt"],
    "gaps_to_exploit": ["CONTENT topics and MESSAGING angles competitors are missing"],
    "avoid": ["MARKETING/CONTENT tactics competitors do that we should NOT copy"]
  }}
}}

CRITICAL: Return ONLY the JSON object, nothing else."""

        print("Calling Claude API for strategy analysis...")
        
        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse response
        strategy_text = message.content[0].text
        
        print(f"Claude response length: {len(strategy_text)} chars")
        
        # Try to extract JSON if wrapped in markdown
        if "```json" in strategy_text:
            strategy_text = strategy_text.split("```json")[1].split("```")[0].strip()
        elif "```" in strategy_text:
            strategy_text = strategy_text.split("```")[1].split("```")[0].strip()
        
        strategy = json.loads(strategy_text)
        
        # Save strategy to PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor()

        # Delete old strategy for this user
        cur.execute("DELETE FROM brand_strategy WHERE user_id = %s", (user_id,))

        # Insert new strategy
        cur.execute("""
            INSERT INTO brand_strategy (
                user_id, brand_voice, messaging_pillars, language_patterns,
                dos_and_donts, target_audience, content_themes, competitive_positioning
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            PgJson(strategy.get('brand_voice', {})),
            strategy.get('messaging_pillars', []),
            PgJson(strategy.get('language_patterns', {})),
            PgJson(strategy.get('dos_and_donts', {})),
            PgJson(strategy.get('target_audience', {})),
            strategy.get('content_themes', []),
            PgJson(strategy.get('competitive_positioning', {}))
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Strategy saved to PostgreSQL")
        
        return {
            "success": True,
            "strategy": strategy,
            "message": f"✅ Analyzed {len(assets)} brand assets" + 
                      (f" and {competitor_summary['analyzed']} competitors" if competitor_summary else "")
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        return {
            "success": False,
            "error": f"Could not parse strategy as JSON. Response preview: {strategy_text[:200]}..."
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Strategy analysis failed: {str(e)}"
        }

@router.get("/current")
async def get_current_strategy(request: Request):
    """Get the current brand strategy from PostgreSQL"""
    user_id = get_user_from_token(request)
    strategy = load_brand_strategy(user_id)
    
    if not strategy:
        return {
            "success": False,
            "error": "No strategy generated yet. Click 'Analyze Brand Voice' to create one."
        }
    
    return {
        "success": True,
        "strategy": strategy
    }

@router.get("/next-keyword")
async def get_next_keyword(request: Request):
    """Get the next strategic keyword to write about based on brand strategy"""
    try:
        user_id = get_user_from_token(request)
        strategy = load_brand_strategy(user_id)

        if not strategy:
            return {
                "recommended_next": {
                    "keyword": "Professional Video Production Services",
                    "search_intent": "Find quality videographers for business content",
                    "market_gap": "Businesses struggle to find vetted, professional videographers"
                }
            }

        # Query existing blog posts to avoid duplicates
        existing_topics = []
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT title, tags
                FROM content_library
                WHERE user_id = %s AND content_type = 'blog'
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for row in rows:
                existing_topics.append(row['title'])
                if row['tags']:
                    existing_topics.extend(row['tags'])
        except Exception as e:
            print(f"Error loading existing topics: {e}")

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        content_themes = ', '.join(strategy.get('content_themes', []))
        messaging_pillars = ', '.join(strategy.get('messaging_pillars', []))

        comp_context = ""
        if 'competitive_positioning' in strategy:
            comp_pos = strategy['competitive_positioning']
            if isinstance(comp_pos, dict):
                gaps = comp_pos.get('gaps_to_exploit', [])
                if gaps:
                    comp_context = f"\nContent gaps to exploit: {', '.join(gaps[:3])}"

        # Build existing topics context
        existing_context = ""
        if existing_topics:
            unique_topics = list(set(existing_topics))[:15]  # Dedupe and limit
            existing_context = f"\n\n🚫 ALREADY COVERED (DO NOT recommend similar topics):\n{chr(10).join(f'- {topic}' for topic in unique_topics)}\n\nIMPORTANT: Recommend a DIFFERENT topic that we have NOT covered yet."

        prompt = f"""Based on Orla³'s brand strategy, recommend the next blog post keyword to target.

Brand Content Themes: {content_themes}
Messaging Pillars: {messaging_pillars}
{comp_context}{existing_context}

Recommend a keyword that:
1. Aligns with our brand themes
2. Exploits competitive content gaps
3. Has commercial intent (people looking to hire videographers)
4. Is specific enough to rank for
5. Is DIFFERENT from topics we've already covered

Return ONLY valid JSON (no markdown):
{{
  "keyword": "specific keyword phrase",
  "search_intent": "what the user wants to accomplish",
  "market_gap": "why this is a strategic opportunity"
}}"""

        # Use GPT-4o-mini for simple keyword recommendation
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(status_code=503, detail="OpenAI API not configured")

        openai_client = OpenAI(api_key=openai_key)

        message = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        response_text = message.choices[0].message.content.strip()
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        recommended = json.loads(response_text)
        
        return {"recommended_next": recommended}
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "recommended_next": {
                "keyword": "Professional Video Production Services",
                "search_intent": "Find quality videographers for business content",
                "market_gap": "Businesses struggle to find vetted, professional videographers"
            }
        }

@router.post("/market-research")
async def market_research(request: Request, data: dict):
    """Analyze market for a given keyword"""
    try:
        user_id = get_user_from_token(request)
        keyword = data.get('keyword', '')
        strategy = load_brand_strategy(user_id)
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        brand_context = ""
        if strategy:
            brand_context = f"""
OUR BRAND (Orla³):
- Messaging: {', '.join(strategy.get('messaging_pillars', []))}
- Target Audience: {strategy.get('target_audience', {}).get('primary', 'Creative professionals') if isinstance(strategy.get('target_audience'), dict) else 'Creative professionals'}
"""
            comp_pos = strategy.get('competitive_positioning', {})
            if isinstance(comp_pos, dict) and comp_pos.get('unique_value'):
                brand_context += f"- Unique Value: {comp_pos.get('unique_value', '')}\n"
        
        prompt = f"""Analyze the content landscape for: "{keyword}"

{brand_context}

Provide market intelligence:
1. What angles do competitors typically cover?
2. What content gaps exist that Orla³ could exploit?
3. What unique angles could Orla³ take?

Return ONLY valid JSON (no markdown):
{{
  "competitor_angles": ["angle1", "angle2", "angle3"],
  "content_gaps": ["gap1", "gap2", "gap3"],
  "orla3_unique_angles": ["unique1", "unique2", "unique3"]
}}"""

        # Use GPT-4o-mini for simple market research
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(status_code=503, detail="OpenAI API not configured")

        openai_client = OpenAI(api_key=openai_key)

        message = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )

        response_text = message.choices[0].message.content.strip()
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        research = json.loads(response_text)
        return research
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "competitor_angles": ["Generic tips", "Equipment", "Pricing"],
            "content_gaps": ["Vetting process", "Quality guarantees", "Community selection"],
            "orla3_unique_angles": ["Curated marketplace", "Transparency", "Quality-first"]
        }
