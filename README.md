# Orla³ Marketing Automation Suite

AI-powered marketing content generation and automation platform for videographers and creative professionals.

## 🎯 Current Features

### ✅ Content Generation
- **Blog Writer** - AI-generated SEO-optimized blog posts with Claude
- **Carousel Creator** - Multi-slide social media content with branded images
- **Social Media Manager** - AI caption generation for Instagram, LinkedIn, Twitter, etc.
- **Competitor Analysis** - Track and analyze competitor strategies with AI insights

### ✅ Brand Voice Training
- **Brand Voice Manager** - Import brand assets from Google Drive
- Train AI on your authentic voice using documents, chat logs, and guidelines
- Automatic Google Drive shortcut resolution

### ✅ Media Management
- **Media Library** - Browse and manage Google Drive assets
- **Folder Navigation** - Deep folder browsing with breadcrumbs
- **Multi-Select** - Select multiple files for social posts
- **Preview & Import** - Preview files in Drive before importing
- **Advanced Filters** - Filter by content type, status, date range, and search

### ✅ Content Library
- View all generated blogs, carousels, and captions in one place
- Filter by type, status, and date
- Search by title
- Preview and copy content

## 🛠️ Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI**: Anthropic Claude Sonnet 4.5
- **Storage**: JSON files (simple, no database required)
- **APIs**: Google Drive API, Unsplash API

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Google Drive API credentials
- Anthropic API key

### Installation

1. Clone and install
```bash
git clone https://github.com/stevenajg93/orla3-marketing-suite-app.git
cd orla3-marketing-suite-app
npm install
cd backend && pip install -r requirements.txt
```

2. Set up `.env` with your API keys

3. Authorize Google Drive
```bash
cd backend && python auth_drive.py
```

### Running

**Frontend:** `npm run dev` → http://localhost:3000  
**Backend:** `cd backend && python main.py` → http://localhost:8000

## 💰 Cost Estimate
- Claude API: ~$10-30/month
- Hosting: Free tier available
- Drive & Unsplash APIs: Free

---
**Ready for production** | Built with ❤️ for videographers and creatives
