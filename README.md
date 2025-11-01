# 🎪 ORLA³ Marketing Suite

AI-powered marketing automation platform for videographers and creative professionals. Generate brand-aligned, strategically positioned content in seconds.

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

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Anthropic API key

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env.local
echo "ANTHROPIC_API_KEY=your-key-here" > .env.local

# Run server
python main.py
```

Backend runs on `http://localhost:8000`

### 2. Frontend Setup
```bash
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

### 3. Initial Setup
1. Navigate to **Brand Voice** → Upload brand guidelines and samples
2. Navigate to **Competitor Analysis** → Add competitors
3. Navigate to **Strategy Planner** → Click "Analyze Brand Voice"
4. Start generating content! 🎉

---

## 🏗️ Architecture
```
Brand Voice Upload → Strategy Planner ← Competitor Analysis
                            ↓
                    brand_strategy.json
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
   Blog Generator    Carousel Creator    Caption Generator
        └───────────────────┼───────────────────┘
                            ↓
                    Content Library
```

### Tech Stack
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI**: Anthropic Claude Sonnet 4.5
- **Storage**: JSON files (MVP - easy migration to PostgreSQL)
- **Integrations**: Google Drive API, Unsplash API

---

## 📊 How It Works

### The Strategy Loop
1. **Upload Brand Materials**: Guidelines, voice samples, community conversations
2. **Add Competitors**: Name, industry, social handles
3. **AI Analysis**: 
   - Analyzes your brand voice, tone, messaging
   - Analyzes competitor content strategies
   - Synthesizes both into unified strategy
4. **Generate Content**: All generators automatically use the strategy
5. **Result**: Content that sounds like YOU and positions against competitors

### What Makes This Different?
- ❌ Generic AI content
- ❌ Copy-paste competitor features
- ✅ **Your authentic brand voice**
- ✅ **Strategic market positioning**
- ✅ **Actionable content gaps**

---

## 🎯 Use Cases

### For Solo Videographers
- Generate SEO blogs to rank for target keywords
- Create Instagram carousels showcasing expertise
- Position against larger competitors (Fiverr, Upwork)

### For Video Production Agencies
- Maintain consistent brand voice across team
- Identify content gaps competitors are missing
- Generate client-facing content at scale

### For Marketers
- Understand competitive landscape
- Exploit market gaps with targeted content
- Train AI on client's actual brand materials

---

## 📁 Project Structure
```
orla3-marketing-suite-app/
├── app/dashboard/           # Frontend pages
│   ├── blog/               # Blog generator
│   ├── carousel/           # Carousel creator
│   ├── social/             # Social manager
│   ├── brand-voice/        # Upload training materials
│   ├── strategy/           # Strategy synthesis
│   └── competitor/         # Competitor analysis
├── backend/
│   ├── routes/             # API endpoints
│   │   ├── draft.py       # Blog generation
│   │   ├── carousel.py    # Carousel creation
│   │   ├── social_caption.py  # Caption generation
│   │   ├── strategy.py    # Strategy synthesis
│   │   └── competitor.py  # Competitor analysis
│   ├── brand_strategy.json      # Generated strategy
│   ├── competitor_data.json     # Competitor analyses
│   └── content_library.json     # Generated content
└── README.md
```

---

## 🔐 Environment Variables

Create `backend/.env.local`:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
UNSPLASH_ACCESS_KEY=...
```

---

## 🎓 Key Concepts

### Brand Strategy File
Central intelligence layer containing:
- Brand voice & tone
- Messaging pillars
- Language patterns (preferred phrases, vocabulary)
- Do's and don'ts
- Target audience
- **Competitive positioning** (unique value, gaps, what to avoid)

### Marketing-Focused Competitor Analysis
Analyzes competitors' **CONTENT & MESSAGING** only:
- ✅ Content themes and topics
- ✅ Messaging strategies
- ✅ Brand voice and tone
- ❌ NOT product features
- ❌ NOT business models

### Strategy-Aware Content Generation
Every piece of content:
1. Loads `brand_strategy.json`
2. Injects brand context into AI prompt
3. Generates content matching your voice
4. Leverages competitive positioning
5. Exploits market gaps

---

## 🐛 Known Limitations

- **JSON Storage**: Not suitable for production scale (migrate to PostgreSQL)
- **Single User**: No authentication system yet
- **No Publishing**: Manual posting required (APIs planned)
- **Competitor Analysis**: Strategic inference, not live scraping
- **No Analytics**: Can't track performance yet

---

## 🚀 Roadmap

### Phase 1: Core Features ✅ (Current)
- [x] Brand voice upload
- [x] Competitor analysis
- [x] Strategy synthesis
- [x] Blog generation
- [x] Carousel creation
- [x] Social captions

### Phase 2: Publishing (Next)
- [ ] Instagram API integration
- [ ] LinkedIn API integration
- [ ] Twitter/X API integration
- [ ] WordPress direct publishing

### Phase 3: Intelligence (Future)
- [ ] Live competitor social scraping
- [ ] Content performance analytics
- [ ] A/B testing framework
- [ ] Advanced research mode (10+ min deep dives)

### Phase 4: Scale (Production)
- [ ] PostgreSQL migration
- [ ] User authentication
- [ ] Multi-tenant support
- [ ] Team collaboration features

---

## 🤝 Contributing

This is a pre-launch MVP. Contributions welcome once public beta launches!

---

## 📄 License

Proprietary - All rights reserved

---

## 📞 Support

For setup issues or questions, see `ORLA3_HANDOFF_PROMPT.md` for detailed documentation.

---

**Built with ❤️ for videographers and creative professionals**

**Status**: Pre-Launch MVP | Version 2.0 | Last Updated: October 31, 2025
