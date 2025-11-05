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
- **Backend**: FastAPI, Python 3.12 (Railway)
- **Database**: PostgreSQL (Railway)
- **AI**: Anthropic Claude Sonnet 4.5
- **APIs**: Google Drive API, Unsplash API

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
- Node.js 18+
- Python 3.12+
- PostgreSQL (or use Railway DB)

### Frontend Setup
```bash
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev  # http://localhost:3000
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python main.py  # http://localhost:8000
```

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

## 🔐 Security Notes

- All API keys stored in environment variables
- CORS configured for Vercel frontend only
- PostgreSQL credentials managed by Railway
- No sensitive data in Git repository

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Built with love by the ORLA³ team. For questions or contributions, open an issue!
