from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
import json
import os
from datetime import datetime
from pathlib import Path

router = APIRouter()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

BRAND_VOICE_INDEX_PATH = "brand_voice_index.json"
BRAND_STRATEGY_PATH = "brand_strategy.json"
COMPETITOR_FILE = "competitor_data.json"

def load_brand_voice_assets():
    """Load all uploaded brand voice assets"""
    if not os.path.exists(BRAND_VOICE_INDEX_PATH):
        return []
    
    with open(BRAND_VOICE_INDEX_PATH, 'r') as f:
        data = json.load(f)
        return data.get('assets', [])

def load_competitor_summary():
    """Load competitor marketing insights summary"""
    if not os.path.exists(COMPETITOR_FILE):
        return None
    
    with open(COMPETITOR_FILE, 'r') as f:
        data = json.load(f)
        competitors = data.get('competitors', [])
        
        if not competitors:
            return None
        
        # Build summary
        analyzed = [c for c in competitors if c.get('analysis')]
        
        if not analyzed:
            return None
        
        summary = {
            'total': len(competitors),
            'analyzed': len(analyzed),
            'competitors': []
        }
        
        for comp in analyzed:
            analysis = comp.get('analysis', {})
            summary['competitors'].append({
                'name': comp['name'],
                'threat_level': analysis.get('threat_level', 'unknown'),
                'marketing_they_do_well': analysis.get('marketing_they_do_well', []),
                'content_gaps': analysis.get('content_gaps', []),
                'positioning_messaging': analysis.get('positioning_messaging', ''),
                'content_opportunities': analysis.get('content_opportunities', [])
            })
        
        return summary

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
async def analyze_brand_voice(include_competitors: bool = True):
    """
    Analyze brand voice assets and optionally include competitive MARKETING intelligence
    """
    try:
        # Load assets
        assets = load_brand_voice_assets()
        
        if not assets:
            return {
                "success": False,
                "error": "No brand voice assets uploaded yet. Please upload training materials first."
            }
        
        # Extract text from files and organize by category
        brand_context = {
            "guidelines": [],
            "voice_samples": [],
            "community": []
        }
        
        print(f"Processing {len(assets)} assets...")
        
        for asset in assets:
            # Try to extract text if not already done
            text = asset.get('full_text', '')
            if not text or text == "":
                print(f"Extracting text from {asset['filename']}...")
                text = extract_text_from_file(asset['path'])
            
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
            elif category in ['community_videographer', 'community_client']:
                brand_context['community'].append({
                    'filename': asset['filename'],
                    'text': text[:1500]
                })
        
        print(f"Context prepared: {len(brand_context['guidelines'])} guidelines, {len(brand_context['voice_samples'])} samples, {len(brand_context['community'])} community files")
        
        # Load competitor MARKETING insights if requested
        competitor_context = ""
        competitor_summary = None
        
        if include_competitors:
            competitor_summary = load_competitor_summary()
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

**COMMUNITY CONVERSATIONS ({len(brand_context['community'])} files):**
{chr(10).join([f"- {item['filename']}: {item['text'][:300]}..." for item in brand_context['community']]) if brand_context['community'] else "None uploaded"}
"""

        prompt = f"""You are a CONTENT MARKETING strategist creating a comprehensive CONTENT & MESSAGING strategy for Orla³.

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
        
        # Add metadata
        strategy['generated_at'] = datetime.now().isoformat()
        strategy['assets_analyzed'] = len(assets)
        strategy['competitors_included'] = competitor_summary['analyzed'] if competitor_summary else 0
        strategy['categories'] = {
            'guidelines': len(brand_context['guidelines']),
            'voice_samples': len(brand_context['voice_samples']),
            'community': len(brand_context['community'])
        }
        
        # Save strategy
        with open(BRAND_STRATEGY_PATH, 'w') as f:
            json.dump(strategy, f, indent=2)
        
        print("✅ Strategy saved successfully")
        
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
async def get_current_strategy():
    """Get the current brand strategy"""
    if not os.path.exists(BRAND_STRATEGY_PATH):
        return {
            "success": False,
            "error": "No strategy generated yet. Click 'Analyze Brand Voice' to create one."
        }
    
    with open(BRAND_STRATEGY_PATH, 'r') as f:
        strategy = json.load(f)
    
    return {
        "success": True,
        "strategy": strategy
    }

@router.get("/next-keyword")
async def get_next_keyword():
    """Get the next strategic keyword to write about based on brand strategy"""
    try:
        strategy = load_brand_strategy()
        
        if not strategy:
            return {
                "recommended_next": {
                    "keyword": "Professional Video Production Services",
                    "search_intent": "Find quality videographers for business content",
                    "market_gap": "Businesses struggle to find vetted, professional videographers"
                }
            }
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        content_themes = ', '.join(strategy.get('content_themes', []))
        messaging_pillars = ', '.join(strategy.get('messaging_pillars', []))
        
        comp_context = ""
        if 'competitive_positioning' in strategy:
            gaps = strategy['competitive_positioning'].get('gaps_to_exploit', [])
            if gaps:
                comp_context = f"\nContent gaps to exploit: {', '.join(gaps[:3])}"
        
        prompt = f"""Based on Orla³'s brand strategy, recommend the next blog post keyword to target.

Brand Content Themes: {content_themes}
Messaging Pillars: {messaging_pillars}
{comp_context}

Recommend a keyword that:
1. Aligns with our brand themes
2. Exploits competitive content gaps
3. Has commercial intent (people looking to hire videographers)
4. Is specific enough to rank for

Return ONLY valid JSON (no markdown):
{{
  "keyword": "specific keyword phrase",
  "search_intent": "what the user wants to accomplish",
  "market_gap": "why this is a strategic opportunity"
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
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
async def market_research(data: dict):
    """Analyze market for a given keyword"""
    try:
        keyword = data.get('keyword', '')
        strategy = load_brand_strategy()
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        brand_context = ""
        if strategy:
            brand_context = f"""
OUR BRAND (Orla³):
- Messaging: {', '.join(strategy.get('messaging_pillars', []))}
- Target Audience: {strategy.get('target_audience', {}).get('primary', 'Creative professionals')}
"""
            if 'competitive_positioning' in strategy:
                brand_context += f"- Unique Value: {strategy['competitive_positioning'].get('unique_value', '')}\n"
        
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

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
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
