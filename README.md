# 🎪 ORLA³ Marketing Suite

AI-powered marketing automation platform for videographers and creative professionals. Generate brand-aligned, strategically positioned content in seconds.

**🚀 Live:** https://orla3-marketing-suite-app.vercel.app

---

## ✨ Key Features

### 🎯 Brand Strategy Intelligence
- **Upload brand voice materials** (guidelines, samples, community conversations)
- **Analyze competitors** with marketing-focused AI analysis
- **Synthesize strategy** combining brand voice + competitive positioning
- **Auto-apply to all content** - every piece sounds like your brand

### 📝 Content Generation Suite
- **Blog Writer**: SEO-optimized articles with auto-keyword selection
- **Carousel Creator**: 7-slide social media carousels (Instagram/LinkedIn)
- **Social Captions**: Platform-aware captions with hashtags
- **All strategy-aware**: Uses your brand voice and competitive positioning

### 🔍 Competitive Intelligence
- **Track competitors** by name and social handles
- **Marketing analysis**: Content strategies, gaps to exploit, positioning
- **Structured insights**: What they do well, what to avoid, opportunities
- **Feeds into strategy**: Automatically influences content generation

### 📁 Media Management
- **Google Drive integration**: Import assets directly
- **Content library**: Filter by type, status, tags
- **Unified dashboard**: All content in one place

---

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS (Vercel)
- **Backend**: FastAPI, Python 3.14+ (Railway)
- **Database**: PostgreSQL (Railway)
- **AI**: Anthropic Claude Sonnet 4.5
- **APIs**: Google Drive API, Unsplash API
- **Node**: v24.10.0, npm 11.6.0

### Clean Architecture
```
lib/
├── config.ts          # Single source of truth for env vars
├── api-client.ts      # Centralized HTTP client
└── storage.ts         # Local storage utilities

backend/
├── routes/            # FastAPI route handlers
│   ├── strategy.py   # Brand strategy (PostgreSQL)
│   ├── library.py    # Content CRUD (PostgreSQL)
│   ├── competitor.py # Competitor analysis (PostgreSQL)
│   └── draft.py      # Blog generation
├── schema.sql        # PostgreSQL schema
└── main.py           # FastAPI app with CORS
```

### Database Schema
- `brand_strategy` - Brand voice, messaging pillars, competitive positioning
- `brand_voice_assets` - Uploaded files with extracted text
- `content_library` - Generated content with metadata
- `competitors` - Competitor profiles and analysis
- `calendar_events` - Content calendar

---

## 🚀 Deployment

### Production URLs
- **Frontend**: https://orla3-marketing-suite-app.vercel.app
- **Backend**: https://orla3-marketing-suite-app-production.up.railway.app

### Environment Variables

**Frontend (Vercel):**
```bash
NEXT_PUBLIC_API_URL=https://orla3-marketing-suite-app-production.up.railway.app
```

**Backend (Railway):**
```bash
DATABASE_URL=postgresql://... (auto-injected by Railway)
ANTHROPIC_API_KEY=sk-...
UNSPLASH_ACCESS_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
# Social media API keys...
```

---

## 💻 Local Development

### Prerequisites
- Node.js 18+ (tested with v24.10.0)
- Python 3.12+ (tested with 3.14.0)
- PostgreSQL (or use Railway DB)

### Quick Start

**1. Clone & Install**
```bash
git clone https://github.com/stevenajg93/orla3-marketing-suite-app.git
cd orla3-marketing-suite-app
npm install
```

**2. Frontend Setup**
```bash
# Create environment file
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev  # Runs on http://localhost:3000
```

**3. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create environment file from template
cp .env.example .env
# Edit .env and add your API keys:
# - DATABASE_URL (required)
# - ANTHROPIC_API_KEY (required)
# - UNSPLASH_ACCESS_KEY
# - Google OAuth credentials

python main.py  # Runs on http://localhost:8000
```

### Daily Workflow
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend
npm run dev

# Open http://localhost:3000
```

**For detailed setup instructions and security best practices, see `SETUP.md`**

---

## 📖 API Documentation

Backend API docs (when running locally): http://localhost:8000/docs

### Key Endpoints
- `POST /strategy/analyze` - Generate brand strategy from uploaded assets
- `POST /draft/content/draft` - Generate blog post with brand voice
- `POST /carousel/social/carousel` - Create 7-slide carousel
- `POST /social-caption/generate-caption` - Generate social media caption
- `GET /library/content` - Fetch all generated content
- `POST /competitor/add` - Add competitor for tracking

---

## 🎨 Brand Voice System

1. **Upload brand materials** (PDFs, DOCX, TXT, images with text)
2. **AI extracts** key phrases, tone, personality
3. **Competitor analysis** identifies positioning gaps
4. **Strategy synthesis** creates comprehensive brand guide
5. **All content generation** uses this strategy automatically

---

## 🔐 Security

### Security Features ✅
- **Zero hardcoded credentials** - All secrets in environment variables only
- **Environment templates** - `.env.example` files provided, actual `.env` files gitignored
- **CORS protection** - Configured for Vercel frontend + localhost only
- **Database security** - PostgreSQL credentials managed by Railway, never committed
- **Type-safe API** - TypeScript type guards prevent runtime errors
- **Proper error handling** - All catch blocks log errors for debugging

### Recent Security Fixes (Nov 2025)
- ✅ Removed exposed Google OAuth credentials from git history
- ✅ Removed hardcoded DATABASE_URL from 13 backend files
- ✅ Implemented proper `os.getenv()` pattern with validation
- ✅ Created comprehensive `.env.example` templates
- ✅ Updated `.gitignore` to prevent future credential exposure
- ✅ Fixed 8 TypeScript type errors for runtime safety

### Setup Security
See `SETUP.md` for detailed security best practices and environment configuration.

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Built with love by the ORLA³ team. For questions or contributions, open an issue!
