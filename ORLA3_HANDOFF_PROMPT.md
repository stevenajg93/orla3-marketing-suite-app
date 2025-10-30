# ORLA³ Marketing Suite - Developer Handoff Prompt

## 🎯 PROJECT OVERVIEW

**Orla³ Marketing Suite** is an AI-powered marketing content generation and automation platform built specifically for videographers and creative professionals. It combines Claude AI with Google Drive integration to streamline content creation workflows.

### Core Value Proposition
- Generate SEO-optimized blogs, social media carousels, and captions with AI
- Train AI on your brand voice using actual business documents
- Manage media assets from Google Drive with intelligent browsing
- Filter and organize all generated content in one place

---

## 🏗️ CURRENT ARCHITECTURE

### Tech Stack
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.9+)
- **AI**: Anthropic Claude Sonnet 4.5
- **Storage**: JSON files (content_library.json, brand_voice_index.json, competitor_data.json)
- **APIs**: Google Drive API, Unsplash API

### Project Structure
```
orla3-marketing-suite-app/
├── app/dashboard/
│   ├── blog/              # Blog post generator
│   ├── carousel/          # Social media carousel creator
│   ├── social/            # Social media manager with Drive import
│   ├── brand-voice/       # Brand voice training system
│   ├── media/             # Media library with filters
│   ├── calendar/          # Content calendar (UI only)
│   ├── competitor/        # Competitor analysis
│   └── page.tsx          # Main dashboard
├── backend/
│   ├── routes/
│   │   ├── blog.py       # Blog generation endpoint
│   │   ├── carousel.py   # Carousel creation endpoint  
│   │   ├── social.py     # Social caption + Drive file resolver
│   │   ├── brand_voice_upload.py  # Brand voice training
│   │   ├── drive.py      # Google Drive integration
│   │   ├── media.py      # Media library API
│   │   ├── competitor.py # Competitor tracking
│   │   └── social_caption.py  # Caption generation
│   ├── brand_voice_assets/  # Uploaded training files
│   ├── credentials/         # Google Drive OAuth tokens
│   ├── main.py             # FastAPI server
│   └── auth_drive.py       # Drive authorization script
└── README.md
```

---

## ✅ IMPLEMENTED FEATURES

### 1. Blog Writer (`/dashboard/blog`)
- AI-generated SEO-optimized blog posts (1500+ words)
- Custom topic, keywords, and tone inputs
- Saves to content library with metadata
- **Status**: WORKING

### 2. Carousel Creator (`/dashboard/carousel`)
- Generates 7-slide social media carousels
- Fetches images from Unsplash API
- Hook → Context → 3 Insights → How-To → CTA structure
- Saves carousel JSON with image URLs
- **Status**: WORKING

### 3. Social Media Manager (`/dashboard/social`)
**Key Features:**
- AI caption generation with Claude
- Google Drive media browser with:
  - Folder navigation (click folders to browse)
  - File preview (opens in Drive in new tab)
  - Multi-select media files
  - Google Drive shortcut resolution
- Selected media preview with type detection
- Platform selection (Instagram, LinkedIn, Twitter, Facebook, TikTok)
- **Status**: WORKING - Drive import fully functional

### 4. Brand Voice Manager (`/dashboard/brand-voice`)
**Capabilities:**
- Import brand assets from Google Drive (docs, PDFs, text files)
- Three training categories:
  - **Guidelines**: Brand style guides, tone docs
  - **Voice Samples**: Blog posts, marketing copy
  - **Community**: Customer conversations, testimonials
- Google Drive shortcut resolution
- File content extraction and indexing
- Stored in `brand_voice_assets/` and `brand_voice_index.json`
- **Status**: WORKING - Import functional, AI integration pending

### 5. Media Library (`/dashboard/media`)
**Three Tabs:**
- **Google Drive Assets**: Browse and download files
- **Unsplash**: Search stock photos
- **Generated Content**: View all created blogs/carousels/captions

**Filters (Generated Content):**
- Search by title
- Filter by content type (Blog, Carousel, Caption)
- Filter by status (Draft, Published, Scheduled)
- Filter by date range (Today, Week, Month, Year)
- Clear all filters button
- **Status**: WORKING

### 6. Competitor Analysis (`/dashboard/competitor`)
- Track competitor profiles
- Store competitor data in JSON
- **Status**: BASIC - UI exists, limited functionality

### 7. Content Calendar (`/dashboard/calendar`)
- Calendar view for scheduled content
- **Status**: UI ONLY - Not functional

---

## 🔧 KEY TECHNICAL IMPLEMENTATIONS

### Google Drive Integration
**Critical Feature: Shortcut Resolution**
```python
# backend/routes/social.py and brand_voice_upload.py
def resolve_drive_shortcut(service, file_id):
    file = service.files().get(fileId=file_id, fields='mimeType,shortcutDetails', supportsAllDrives=True).execute()
    if file.get('mimeType') == 'application/vnd.google-apps.shortcut':
        return file['shortcutDetails']['targetId'], file['shortcutDetails']['targetMimeType']
    return file_id, file.get('mimeType')
```

**Why This Matters:**
- Google Drive shortcuts are references, not actual files
- Direct download of shortcuts fails
- Must resolve to target file ID first
- Used in both Brand Voice uploads and Social Manager

### Multi-Select Media (Social Manager)
**Frontend Pattern:**
```typescript
// Stores media as objects with metadata
const mediaItem = {
  url: string,
  type: string,  // MIME type
  name: string,
  source: 'drive',
  folder: string
};
setSelectedMedia([...selectedMedia, mediaItem]);  // Append, don't replace
```

### Content Library Storage
**Files:**
- `backend/content_library.json` - All generated content
- `backend/brand_voice_index.json` - Brand voice training data
- `backend/competitor_data.json` - Competitor tracking

**Structure:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "content_type": "blog|carousel|caption",
      "content": "string|json",
      "status": "draft|published|scheduled",
      "created_at": "ISO date",
      "tags": ["array"]
    }
  ]
}
```

---

## 🚧 KNOWN LIMITATIONS & TODO

### High Priority
- [ ] **Brand Voice AI Integration**: Training files are indexed but not used in generation yet
- [ ] **Social Publishing**: "Post Now" button doesn't actually post to platforms
- [ ] **Media Player**: Selected media shows icons, not actual image/video preview
- [ ] **Authentication**: No user login system
- [ ] **Database**: Using JSON files, should migrate to Supabase/PostgreSQL

### Medium Priority
- [ ] **Calendar Functionality**: Make calendar interactive with drag-drop scheduling
- [ ] **Competitor Scraping**: Actually fetch competitor data from social platforms
- [ ] **Analytics Integration**: Connect Google Analytics/Search Console
- [ ] **Content Refresh Detection**: Find underperforming content to update

### Low Priority
- [ ] **Team Collaboration**: User roles, approval workflows
- [ ] **A/B Testing**: Test different headlines/CTAs
- [ ] **Email Automation**: Newsletter generation
- [ ] **CRM Integration**: Link contacts to campaigns

---

## 🔑 ENVIRONMENT SETUP

### Required Environment Variables (.env)
```bash
ANTHROPIC_API_KEY=sk-ant-...
UNSPLASH_ACCESS_KEY=your_unsplash_key
SHARED_DRIVE_ID=your_google_drive_id
SHARED_DRIVE_NAME=Marketing
MARKETING_FOLDER_NAME=Marketing
```

### Google Drive Setup
1. Create Google Cloud Project
2. Enable Google Drive API
3. Create OAuth 2.0 credentials
4. Download as `credentials.json`
5. Place in `backend/credentials/`
6. Run `python backend/auth_drive.py`
7. Authorize in browser
8. Token saved as `backend/credentials/token.pickle`

### Running Locally
**Terminal 1 - Frontend:**
```bash
cd ~/Desktop/orla3-marketing-suite-app
npm run dev
# http://localhost:3000
```

**Terminal 2 - Backend:**
```bash
cd ~/Desktop/orla3-marketing-suite-app/backend
python main.py
# http://localhost:8000
```

---

## 👤 USER: Steven

### Working Style
- **Preference**: Terminal commands on macOS
- **Location**: Lisbon, Portugal (Europe/London timezone)
- **Shell**: zsh
- **Approach**: Step-by-step instructions, one command at a time
- **Needs**: Clear explanations, expected outcomes

### Communication Style
- ✅ Use emojis for visual scanning
- 📝 One command per message
- 🎯 Show expected output
- 🔧 Debug collaboratively
- 🚀 Celebrate wins

---

## 🎯 NEXT DEVELOPMENT PRIORITIES

### Sprint 1: Brand Voice Integration (Week 1)
1. Load brand voice context from index
2. Inject into blog/carousel/caption prompts
3. Test voice consistency across generations

### Sprint 2: Social Publishing (Week 2)
4. Add platform API credentials (Instagram, LinkedIn, Twitter)
5. Implement actual post publishing
6. Handle rate limits and errors
7. Store post IDs for tracking

### Sprint 3: Media Preview (Week 1)
8. Add image viewer in Social Manager
9. Add video player for video files
10. Show actual previews instead of icons

### Sprint 4: Database Migration (Week 2)
11. Set up Supabase project
12. Design schema (posts, media, users, analytics)
13. Migrate from JSON to PostgreSQL
14. Add proper migrations

### Sprint 5: Authentication (Week 1)
15. Add Supabase Auth
16. Implement login/signup
17. Protect routes
18. User-specific content

---

## 📚 IMPORTANT PATTERNS

### API Response Format
All backend endpoints return:
```json
{
  "success": true/false,
  "data": {...},
  "error": "message" (if failed)
}
```

### Error Handling
```python
try:
    # operation
    return {"success": True, "data": result}
except Exception as e:
    return {"success": False, "error": str(e)}
```

### Frontend Fetch Pattern
```typescript
const res = await fetch('http://localhost:8000/endpoint');
const data = await res.json();
if (data.success) {
  // handle success
} else {
  alert(data.error);
}
```

---

## 🎓 DEVELOPER ONBOARDING

### Day 1: Environment Setup
1. Clone repo
2. Install dependencies (npm + pip)
3. Set up .env
4. Authorize Google Drive
5. Run frontend + backend
6. Test blog generation

### Day 2: Code Exploration
7. Read this handoff prompt fully
8. Explore dashboard UI structure
9. Review backend routes
10. Test Drive import in Brand Voice + Social

### Day 3: First Contribution
11. Pick a TODO item
12. Create feature branch
13. Implement + test
14. Create PR with description

---

## ✅ PROJECT STATUS SUMMARY

**What's Working:**
- Core content generation (Blog, Carousel, Social Captions)
- Google Drive integration with shortcut resolution
- Media library with advanced filtering
- Brand voice file imports (indexing only)
- Multi-select media in Social Manager

**What's Not Working:**
- Brand voice not used in AI generation yet
- Social posts don't actually publish
- Media preview shows icons not actual media
- Calendar is UI-only
- No authentication or user management

**Overall Assessment:**
Solid MVP foundation with AI generation and Drive integration working. Ready for next phase of development focusing on integration and polish.

---

**Last Updated**: October 30, 2025  
**Maintained By**: Steven Gillespie  
**Repository**: https://github.com/stevenajg93/orla3-marketing-suite-app
