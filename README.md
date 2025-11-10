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
- **Blog Writer**: SEO-optimized articles with auto-keyword selection (Claude Sonnet 4)
- **Carousel Creator**: 7-slide social media carousels (Gemini 2.0 Flash)
- **Social Captions**: Platform-aware captions with hashtags (GPT-4o)
- **Ad Copy Generator**: Multi-platform ad campaigns (GPT-4o)
- **Comment Replies**: AI-powered engagement responses (GPT-4o)
- **Blog Atomization**: Convert blogs to 8 platform-specific posts (Gemini 2.0 Flash)
- **All strategy-aware**: Uses your brand voice and competitive positioning

### 🔍 Competitive Intelligence
- **Track competitors** by name and social handles
- **Automated research**: Perplexity AI scrapes real competitor marketing content
- **Marketing analysis**: Content strategies, gaps to exploit, positioning (Claude Sonnet 4)
- **Market-based threat assessment**: Identifies direct vs indirect competitors
- **Structured insights**: What they do well, what to avoid, opportunities
- **Feeds into strategy**: Automatically influences content generation

### 📁 Media Management
- **Google Drive integration**: Import assets directly
- **AI Image Generation**: Google Imagen 3 via Vertex AI ($0.02-0.04/image)
- **AI Video Generation**: Google Veo via Vertex AI (experimental, may require allowlist)
- **Content library**: Filter by type, status, tags
- **Unified dashboard**: All content in one place

### 📢 Social Media Publishing
- **9 Platform Support**: Instagram, LinkedIn, Twitter/X, Facebook, TikTok, YouTube, Reddit, Tumblr, WordPress
- **Working**: Twitter/X, WordPress
- **Ready (needs tokens)**: Instagram, LinkedIn, Facebook, Reddit, Tumblr
- **Video platforms**: TikTok, YouTube (coming soon)
- **Universal API**: Single endpoint for all platforms

---

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS (Vercel)
- **Backend**: FastAPI, Python 3.14+ (Railway)
- **Database**: PostgreSQL (Railway)
- **AI**: Multi-provider optimization
  - **Perplexity AI**: Real-time web research
  - **Claude Sonnet 4**: Strategic analysis & brand-critical content
  - **GPT-4o**: Creative conversational content
  - **Gemini 2.0 Flash**: Structured visual content
  - **Imagen 3**: AI image generation (Vertex AI)
  - **Google Veo**: AI video generation (Vertex AI, experimental)
  - **GPT-4o-mini**: Simple analytical tasks
- **APIs**: Google Drive API, Unsplash API
- **Publishing**: 9 social platforms (Instagram, LinkedIn, Twitter/X, Facebook, TikTok, YouTube, Reddit, Tumblr, WordPress)
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

# AI Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...
PERPLEXITY_API_KEY=pplx-...

# Media
UNSPLASH_ACCESS_KEY=...

# Google Drive OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Social Media Publishing (optional)
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_PERSON_URN=...
TWITTER_API_KEY=...
TWITTER_ACCESS_TOKEN=...
FACEBOOK_PAGE_ACCESS_TOKEN=...
FACEBOOK_PAGE_ID=...
REDDIT_CLIENT_ID=...
TUMBLR_API_KEY=...
WORDPRESS_SITE_URL=...
# ...and more
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

**Strategy & Analysis**
- `POST /strategy/analyze` - Generate brand strategy from uploaded assets (Claude Sonnet 4)
- `GET /strategy/next-keyword` - AI-selected next keyword (GPT-4o-mini)
- `POST /strategy/market-research` - Keyword research (GPT-4o-mini)

**Content Generation**
- `POST /draft/content/draft` - Generate blog post with brand voice (Claude Sonnet 4)
- `POST /carousel/social/carousel` - Create 7-slide carousel (Gemini 2.0 Flash)
- `POST /social-caption/generate-caption` - Generate social media caption (GPT-4o)
- `POST /social-caption/trending-topics` - Research trending topics (Perplexity AI)
- `POST /atomize/blog-to-social` - Convert blog to 8 platform posts (Gemini 2.0 Flash)
- `POST /ads/generate` - Generate ad campaign (GPT-4o)
- `POST /comments/generate-replies` - AI comment replies (GPT-4o)

**Competitor Intelligence**
- `POST /competitor/add` - Add competitor for tracking
- `POST /competitor/{id}/analyze` - Analyze competitor (Claude Sonnet 4 + Perplexity AI)
- `GET /competitor/insights` - Cross-competitor insights (Claude Sonnet 4)

**Social Publishing**
- `POST /publisher/publish` - Publish to any platform (universal endpoint)
- `GET /publisher/status-all` - Check platform configuration status

**Library & Assets**
- `GET /library/content` - Fetch all generated content
- `POST /brand-voice/upload` - Upload brand assets

**AI Generation**
- `POST /ai/generate-image` - Generate image with Google Imagen 3
- `POST /ai/generate-video` - Generate video with Google Veo 3.1
- `GET /ai/video-status/{job_id}` - Check video generation status

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

### Recent Updates (Nov 2025)

**AI Image & Video Generation (Nov 7, 2025)**
- ✅ Google Imagen 3 integration for text-to-image generation ($0.03/image)
- ✅ Google Veo 3.1 integration for text-to-video generation ($6 per 8s video)
- ✅ Added to both Media Library and Social Manager
- ✅ Aspect ratio options: 1:1, 16:9, 9:16, 4:3, 3:4
- ✅ Video resolution options: 720p HD, 1080p Full HD
- ✅ Gallery views with download and preview functionality

**AI Model Optimization (Nov 7, 2025)**
- ✅ Implemented multi-provider AI strategy for 60-75% cost reduction
- ✅ OpenAI GPT-4o for creative conversational content (captions, comments, ads)
- ✅ Gemini 2.0 Flash for structured visual content (carousels, atomization)
- ✅ GPT-4o-mini for simple analytical tasks (15x cheaper than Sonnet 4)
- ✅ Claude Sonnet 4 reserved for strategic/brand-critical work
- ✅ Perplexity AI for real-time competitor research

**Competitor Analysis Enhancement (Nov 7, 2025)**
- ✅ Fixed threat level assessment to evaluate market competition (not just marketing similarity)
- ✅ Automated research with Perplexity AI for real competitor content analysis
- ✅ Direct competitors now correctly identified regardless of marketing tactics

**Social Media Integration (Nov 7, 2025)**
- ✅ 9-platform publishing infrastructure (Instagram, LinkedIn, Twitter/X, Facebook, TikTok, YouTube, Reddit, Tumblr, WordPress)
- ✅ Twitter/X and WordPress fully functional
- ✅ Universal publishing API endpoint

**Security Fixes (Nov 6, 2025)**
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
