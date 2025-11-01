# ORLA³ Marketing Suite - Developer Handoff Prompt

## 🎯 PROJECT OVERVIEW

**Orla³ Marketing Suite** is an AI-powered marketing content generation and automation platform built specifically for videographers and creative professionals. It combines Claude AI with brand strategy intelligence and Google Drive integration to create authentically branded, strategically positioned content.

### Core Value Proposition
- **Brand-Aware Content Generation**: AI learns your brand voice and competitive positioning to create authentic content
- **Strategic Intelligence**: Competitor analysis feeds into content strategy automatically
- **Comprehensive Content Suite**: SEO-optimized blogs, social media carousels, and captions
- **Media Management**: Google Drive integration with intelligent asset browsing
- **Unified Library**: Filter and organize all generated content in one place

---

## 🏗️ CURRENT ARCHITECTURE

### Tech Stack
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.9+)
- **AI**: Anthropic Claude Sonnet 4.5
- **Storage**: JSON files (content_library.json, brand_voice_index.json, brand_strategy.json, competitor_data.json)
- **APIs**: Google Drive API, Unsplash API

### Project Structure
```
orla3-marketing-suite-app/
├── app/dashboard/
│   ├── blog/              # Blog post generator (auto + manual modes)
│   ├── carousel/          # Social media carousel creator
│   ├── social/            # Social media manager with Drive import
│   ├── brand-voice/       # Brand voice training system
│   ├── strategy/          # Strategy Planner (NEW - synthesizes brand + competitors)
│   ├── competitor/        # Competitor marketing analysis
│   ├── media/             # Media library with filters
│   ├── calendar/          # Content calendar
│   └── page.tsx          # Main dashboard
├── backend/
│   ├── routes/
│   │   ├── draft.py           # Blog generation (strategy-aware)
│   │   ├── carousel.py        # Carousel creation (strategy-aware)
│   │   ├── social_caption.py  # Caption generation (strategy-aware)
│   │   ├── strategy.py        # Strategy synthesis + keyword research
│   │   ├── competitor.py      # Marketing-focused competitor analysis
│   │   ├── brand_voice_upload.py  # Brand voice training
│   │   ├── drive.py           # Google Drive integration
│   │   ├── library.py         # Content library management
│   │   └── social.py          # Social posting + Drive resolver
│   ├── brand_voice_assets/    # Uploaded training files
│   ├── brand_strategy.json    # Synthesized strategy (NEW)
│   ├── competitor_data.json   # Competitor analyses
│   ├── content_library.json   # Generated content
│   ├── credentials/           # Google Drive OAuth
│   ├── main.py               # FastAPI server
│   └── auth_drive.py         # Drive authorization
└── README.md
```

---

## 🎪 KEY FEATURES & WORKFLOWS

### 1️⃣ Brand Strategy System (Core Intelligence Layer)

**Purpose**: Create a unified brand strategy that combines brand voice analysis with competitive intelligence.

**Workflow**:
1. User uploads brand voice assets (guidelines, voice samples, community conversations)
2. User adds competitors and runs marketing analysis
3. Strategy Planner synthesizes both into `brand_strategy.json` containing:
   - Brand voice & tone
   - Messaging pillars
   - Language patterns
   - Target audience
   - **Competitive positioning** (unique value, gaps to exploit, what to avoid)

**Files Involved**:
- `backend/routes/strategy.py` - Strategy synthesis endpoints
- `backend/routes/brand_voice_upload.py` - Asset upload
- `backend/brand_strategy.json` - Generated strategy
- `app/dashboard/strategy/page.tsx` - Strategy UI

**Key Endpoints**:
- `POST /strategy/analyze` - Analyze brand voice + competitors → generate strategy
- `GET /strategy/current` - Retrieve current strategy
- `GET /strategy/next-keyword` - AI picks next strategic blog keyword
- `POST /strategy/market-research` - Competitive content analysis for keywords

---

### 2️⃣ Competitor Analysis (Marketing Intelligence)

**Purpose**: Analyze competitors' CONTENT & MESSAGING strategy (not product features).

**Workflow**:
1. User adds competitor (name, industry, social handles)
2. Clicks "Analyze Competitor"
3. AI generates marketing-focused analysis:
   - What content/messaging works for them
   - Content gaps they're missing
   - How to position against them
   - Content opportunities

**Files Involved**:
- `backend/routes/competitor.py` - Competitor CRUD + analysis
- `backend/competitor_data.json` - Stored analyses
- `app/dashboard/competitor/page.tsx` - Competitor UI

**Key Features**:
- Marketing-focused (not product/business model recommendations)
- Brand-aware (uses Orla³ positioning in analysis)
- Structured data (threat level, gaps, opportunities)
- Expandable UI cards showing full breakdown

**CRITICAL**: Analysis focuses on content strategy, messaging, and marketing tactics ONLY.

---

### 3️⃣ Content Generation (Strategy-Aware)

**Purpose**: Generate blogs, carousels, and social captions that sound like YOUR brand and leverage competitive positioning.

#### Blog Generator (`draft.py`)
- **Auto-Generate Mode**: AI picks strategic keyword → market research → generates blog
- **Manual Mode**: User provides keyword + search intent
- **Strategy Integration**: Loads `brand_strategy.json` and injects:
  - Brand voice, tone, personality
  - Messaging pillars
  - Language patterns
  - Competitive positioning
  - Target audience

**Key Rules**:
- NO hashtags in blog content
- NO Markdown headers (##, ###) - plain text sections only
- UK English
- Human-like writing (no corporate jargon, varied sentences)

#### Carousel Creator (`carousel.py`)
- 7-slide format for Instagram/LinkedIn
- Integrates brand strategy throughout all slides
- Unsplash image integration
- Hashtags allowed in captions only

#### Social Caption Generator (`social_caption.py`)
- Platform-aware (X, Instagram, LinkedIn, Facebook)
- Character limit compliance
- Brand voice + competitive positioning
- Hashtags included (appropriate for social)

---

### 4️⃣ Brand Voice Upload System

**Purpose**: Train AI on your actual brand materials.

**Supported File Types**:
- Guidelines: PDF, DOCX, TXT
- Voice Samples: MD, TXT, HTML
- Community: Discord/Slack exports (XLSX, CSV)

**Categories**:
- `guidelines` - Brand guidelines, style guides
- `voice_samples` - Example content
- `community_videographer` - Community conversations (videographer side)
- `community_client` - Community conversations (client side)

**Storage**: `/backend/brand_voice_assets/[category]/`

**Index**: `brand_voice_index.json` tracks all uploaded files with metadata

---

### 5️⃣ Google Drive Integration

**Purpose**: Import media assets from Google Drive into content creation.

**Features**:
- OAuth 2.0 authentication
- Folder navigation
- Image preview
- Direct import to Social Manager

**Auth Flow**:
1. Run `python backend/auth_drive.py`
2. Complete OAuth in browser
3. Tokens stored in `backend/credentials/token.json`

**Key Endpoints**:
- `GET /drive/auth` - Initiate OAuth
- `GET /drive/folders` - List folders
- `GET /drive/files` - List files in folder
- `POST /drive/resolve-url` - Get direct image URLs

---

### 6️⃣ Media Library

**Purpose**: Centralized content management with filtering.

**Features**:
- Filter by type (blog, carousel, social)
- Filter by status (draft, published)
- Search by tags
- View/edit/delete content

**Storage**: `backend/content_library.json`

**Structure**:
```json
{
  "id": "timestamp",
  "title": "Content title",
  "content_type": "blog|carousel|social",
  "content": "Full content",
  "status": "draft|published",
  "tags": ["tag1", "tag2"],
  "created_at": "ISO timestamp"
}
```

---

## 🔐 ENVIRONMENT VARIABLES

Required in `backend/.env.local`:
```bash
# AI
ANTHROPIC_API_KEY=sk-ant-...

# Google Drive (Optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Unsplash (Optional - has fallback)
UNSPLASH_ACCESS_KEY=...
```

---

## 🚀 SETUP & RUN

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs on: `http://localhost:8000`

### Frontend Setup
```bash
npm install
npm run dev
```

Frontend runs on: `http://localhost:3000`

### Google Drive Setup (Optional)
```bash
cd backend
python auth_drive.py
# Complete OAuth in browser
```

---

## 📊 DATA FLOW DIAGRAM
```
Brand Voice Upload → brand_voice_assets/ → Strategy Planner
                                                ↓
Competitor Analysis → competitor_data.json → Strategy Planner
                                                ↓
                                        brand_strategy.json
                                                ↓
                      ┌─────────────────────────┼─────────────────────────┐
                      ↓                         ↓                         ↓
              Blog Generator              Carousel Creator        Caption Generator
                      ↓                         ↓                         ↓
                            Content Library (content_library.json)
```

---

## 🎯 CRITICAL DESIGN DECISIONS

### Why JSON Storage?
- **MVP Speed**: No database setup required
- **Portability**: Easy to migrate data
- **Simplicity**: Direct file access for debugging
- **Future**: Easy migration path to PostgreSQL/MongoDB

### Why Strategy-First Architecture?
- **Quality**: Content sounds authentically like the brand
- **Differentiation**: Competitive positioning baked into every piece
- **Consistency**: Single source of truth for brand voice
- **Scalability**: Add new generators that automatically use strategy

### Why Marketing-Focused Competitor Analysis?
- **User Need**: Marketers need content strategy, not product roadmaps
- **Actionable**: Focus on what they can actually use (content ideas, messaging)
- **Ethical**: Avoid suggesting copying business models/features

---

## 🐛 KNOWN LIMITATIONS & FUTURE WORK

### Current Limitations
1. **No Database**: JSON files limit concurrency and search
2. **No Authentication**: Single-user system
3. **No Publishing**: Content must be manually posted
4. **Competitor Analysis**: Strategic inference, not live social scraping
5. **No Analytics**: Can't track content performance

### Planned Enhancements
1. **Social Publishing APIs**: Direct post to Instagram, LinkedIn, Twitter
2. **Live Competitor Scraping**: Real-time social media data collection
3. **User Authentication**: Multi-tenant support
4. **Database Migration**: PostgreSQL for production scale
5. **Analytics Dashboard**: Track content performance
6. **Advanced Research Mode**: 10+ minute deep research sessions
7. **WordPress Integration**: Direct blog publishing

---

## 🔧 DEBUGGING TIPS

### Backend Issues
```bash
# Check logs
cd backend && python main.py
# Look for: "✅ Anthropic API: Configured"

# Test endpoint directly
curl http://localhost:8000/strategy/current
```

### Strategy Not Loading
```bash
# Check if file exists
ls -la backend/brand_strategy.json

# View strategy
cat backend/brand_strategy.json | python -m json.tool
```

### Drive Integration Not Working
```bash
# Re-authenticate
cd backend && python auth_drive.py

# Check token
cat backend/credentials/token.json
```

### Content Generation Issues
- Check `brand_strategy.json` exists and has `competitive_positioning` section
- Verify Anthropic API key is valid
- Check backend logs for JSON parsing errors
- Ensure strategy was generated AFTER competitors were analyzed

---

## 📞 HANDOFF NOTES

### What Works Well
✅ Brand strategy synthesis is solid  
✅ Content generators produce high-quality, on-brand output  
✅ Competitor analysis provides actionable insights  
✅ UI is intuitive and visually appealing  
✅ Google Drive integration is smooth  

### What Needs Attention
⚠️ No error handling for expired Drive tokens  
⚠️ Large files (>50MB) in Git repo (brand PDFs)  
⚠️ No rate limiting on AI API calls  
⚠️ Content library could get large (needs pagination)  
⚠️ Competitor analysis is inference-based, not live data  

### Quick Wins for Next Developer
1. Add pagination to Media Library (>50 items gets slow)
2. Implement social publishing APIs (high user value)
3. Add live competitor scraping (moderate effort, high value)
4. Database migration (needed for multi-user)
5. Add error boundaries in React components

---

## 🎓 KEY LEARNINGS

1. **AI Context Matters**: Loading brand strategy into prompts dramatically improves output quality
2. **Structured Data > Text**: Competitor analysis as structured JSON enables better synthesis
3. **User Trust**: Transparent about what AI can/can't do (inference vs live data)
4. **Iterative Prompting**: Multiple rounds of prompt refinement to eliminate hashtags, headers, etc.
5. **Marketing Focus**: Users want content strategy, not product recommendations

---

## 📚 ADDITIONAL RESOURCES

- **Anthropic Claude Docs**: https://docs.anthropic.com
- **Next.js 15 Docs**: https://nextjs.org/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Google Drive API**: https://developers.google.com/drive

---

**Last Updated**: October 31, 2025  
**Version**: 2.0 (Strategy-Aware Content Generation)  
**Status**: Pre-Launch MVP - Core features complete, ready for user testing
