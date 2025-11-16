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

### 💳 Payment & Credit System
- **Stripe Integration**: Secure subscription and credit purchases
- **4 Subscription Tiers**: Starter (£25), Professional (£75), Business (£150), Enterprise (£300)
- **Credit-Based Usage**: All AI operations deducted from monthly allocation
- **Credit Top-Ups**: Buy additional credits when needed (500-5000 credits)
- **Real-Time Balance**: Live credit display in dashboard header
- **Usage Tracking**: Complete transaction history and audit trail
- **Email Verification**: Pay-to-access model with email verification gate
- **Customer Portal**: Self-service billing management via Stripe

### 📁 Media Management & Cloud Storage
- **Multi-Cloud Integration**: Google Drive, Dropbox, OneDrive
- **OAuth 2.0 Authentication**: Secure per-user cloud storage connections
- **Folder-Level Privacy**: Users can limit access to specific folders (e.g., company drive only)
- **Secure Token Revocation**: OAuth tokens properly revoked on disconnect
- **File Browsing**: Browse and import files from all connected cloud providers
- **AI Image Generation**: Google Imagen 4 Ultra (20 credits per image)
- **AI Video Generation**: Google Veo 3.1 (200 credits per 8s video with audio)
- **Content library**: Filter by type, status, tags
- **Unified dashboard**: All content in one place

### 📢 Social Media Publishing & Engagement
- **9 Platform Support**: Instagram, LinkedIn, Twitter/X, Facebook, TikTok, YouTube, Reddit, Tumblr, WordPress
- **OAuth 2.0 Multi-Tenant**: Users connect their own accounts securely
- **Platform Status**:
  - ✅ **Twitter/X: WORKING** - Full OAuth 2.0 with PKCE + publishing
  - ✅ **Facebook: WORKING** - Full multi-tenant architecture with Page management + publishing
  - ✅ **Instagram: WORKING** - Full OAuth 2.0 + publishing for Business/Creator accounts
  - ✅ **LinkedIn: WORKING** - OpenID Connect OAuth 2.0 + publishing
  - ✅ **Tumblr: WORKING** - OAuth 2.0 + publishing
  - ✅ **YouTube: WORKING** - Google OAuth 2.0 + video uploads
  - ✅ **Reddit: WORKING** - OAuth 2.0 + post submission
  - ✅ **WordPress.com: WORKING** - OAuth 2.0 + blog publishing
  - ⏳ **TikTok: IN REVIEW** - OAuth 2.0 configured, awaiting app approval (1-3 days)
- **8/9 Platforms Live**: All platforms except TikTok fully operational
- **AI Comment Replies**: Automatically generate brand-aligned responses to comments across all platforms
- **Social Discovery**: Search non-follower posts by keywords and trends to engage with relevant conversations
- **Trends Search**: Real-time trending topics discovery to inform content strategy and engagement timing
- **Database**: Per-user tokens stored encrypted in connected_services table
- **PKCE Security**: Twitter OAuth 2.0 with SHA256 code challenge
- **Facebook Pages**: Users can select which Page to post to, credentials stored in service_metadata
- **Instagram**: Uses Facebook Login API with instagram_basic, instagram_content_publish, instagram_manage_messages
- **Universal API**: Single endpoint for all platforms

---

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS (Vercel)
- **Backend**: FastAPI, Python 3.14+ (Railway)
- **Database**: PostgreSQL (Railway)
- **Authentication**: JWT tokens, bcrypt password hashing
- **Payments**: Stripe (subscriptions, credit purchases)
- **AI**: Multi-provider optimization
  - **Perplexity AI**: Real-time web research
  - **Claude Sonnet 4**: Strategic analysis & brand-critical content
  - **GPT-4o**: Creative conversational content
  - **Gemini 2.0 Flash**: Structured visual content
  - **Imagen 4 Ultra**: AI image generation (Vertex AI)
  - **Veo 3.1**: AI video generation (Vertex AI)
  - **GPT-4o-mini**: Simple analytical tasks
- **APIs**: Google Drive API, Unsplash API, Pexels API, OAuth 2.0
- **Publishing**: 9 social platforms (8/9 live: Instagram, LinkedIn, Twitter/X, Facebook, YouTube, Reddit, Tumblr, WordPress; TikTok in review)
- **Node**: v24.10.0, npm 11.6.0

### Clean Architecture
```
lib/
├── config.ts          # Single source of truth for env vars
├── api-client.ts      # Centralized HTTP client
└── storage.ts         # Local storage utilities

backend/
├── routes/            # FastAPI route handlers
│   ├── auth.py       # User authentication (JWT, bcrypt)
│   ├── strategy.py   # Brand strategy (PostgreSQL)
│   ├── library.py    # Content CRUD (PostgreSQL)
│   ├── competitor.py # Competitor analysis (PostgreSQL)
│   ├── draft.py      # Blog generation
│   ├── carousel.py   # Social carousel generation
│   ├── social_caption.py # Social media captions
│   ├── atomize.py    # Blog-to-social atomization
│   ├── ads.py        # Ad campaign generation
│   ├── comments.py   # AI comment replies
│   ├── publisher.py  # Multi-platform publishing
│   ├── ai_generation.py # Image/video generation
│   ├── oauth.py      # OAuth flows (Google Drive, etc.)
│   ├── drive.py      # Google Drive integration
│   ├── brand_voice_upload.py # Brand asset uploads
│   ├── calendar.py   # Content calendar
│   ├── social.py     # Social media utilities
│   ├── collaboration.py # Team collaboration
│   ├── crm.py        # CRM integration
│   └── primer.py     # Onboarding/primers
├── middleware/       # User context, CORS
├── schema.sql        # PostgreSQL schema
└── main.py           # FastAPI app with CORS
```

### Database Schema
- `users` - User accounts with JWT authentication, subscription plans, and credit balances
- `credit_transactions` - Complete audit trail of all credit operations
- `brand_strategy` - Brand voice, messaging pillars, competitive positioning (per user)
- `brand_voice_assets` - Uploaded files with extracted text (per user)
- `content_library` - Generated content with metadata (per user)
- `competitors` - Competitor profiles and analysis (per user)
- `calendar_events` - Content calendar (per user)

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

# Cloud Storage OAuth 2.0 (Multi-Tenant - Per-User Connections)
# Users connect their own cloud storage via /dashboard/settings/cloud-storage
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
DROPBOX_APP_KEY=...
DROPBOX_APP_SECRET=...
ONEDRIVE_CLIENT_ID=...
ONEDRIVE_CLIENT_SECRET=...

# Social Media OAuth 2.0 (Multi-Tenant - Per-User Connections)
# Users connect their own accounts via /dashboard/settings/social-accounts
INSTAGRAM_CLIENT_ID=...
INSTAGRAM_CLIENT_SECRET=...
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
TWITTER_CLIENT_ID=...
TWITTER_CLIENT_SECRET=...
FACEBOOK_CLIENT_ID=...
FACEBOOK_CLIENT_SECRET=...
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
TUMBLR_CONSUMER_KEY=...
TUMBLR_CONSUMER_SECRET=...
WORDPRESS_CLIENT_ID=...
WORDPRESS_CLIENT_SECRET=...
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

### Automation Scripts
```bash
npm run orla:automate  # Daily content generation automation
npm run orla:report    # Generate analytics report
npm run orla:engage    # Automated engagement
```

The daily automation script (`scripts/daily.js`) can be scheduled via cron for hands-free content generation.

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
- `POST /ai/generate-image` - Generate image with Google Imagen 4 Ultra
- `POST /ai/generate-video` - Generate video with Google Veo 3.1
- `GET /ai/video-status/{job_id}` - Check video generation status

---

## 🔐 Authentication & Multi-User

**User Management:**
- JWT-based authentication with bcrypt password hashing
- User context middleware (all requests scoped to authenticated user)
- Secure signup/login/token refresh endpoints
- Per-user data isolation (strategies, content, competitors, calendar)

**Endpoints:**
- `POST /auth/signup` - Register new account
- `POST /auth/login` - User login (returns JWT)
- `POST /auth/refresh` - Refresh authentication token

All generated content, brand strategies, and competitor analyses are scoped to the authenticated user.

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

**Organization Multi-Tenancy & Team Collaboration! 🎉 (Nov 16, 2025)**
- ✅ **Organization Architecture** - Full team collaboration with role-based access control
- ✅ **Migration 011 Completed** - All users migrated to organization structure
- ✅ **Team Roles** - Owner, Admin, Member, Viewer permissions (owner > admin > member > viewer)
- ✅ **User Limits by Tier** - Starter (1), Professional (3), Business (10), Enterprise (25+)
- ✅ **Organization Tables** - organizations, organization_members, organization_files
- ✅ **Shared Drive Support** - Google Shared Drives, OneDrive SharePoint, Dropbox Teams integration
- ✅ **ORLA³ Native Storage** - Fallback cloud storage with per-tier quotas (5GB-100GB)
- ✅ **Database Column Fixes** - Fixed `selected_folders` (now in metadata jsonb), `created_at` → `connected_at`
- ✅ **Cloud Storage Working** - Google Drive files loading correctly for all users
- ✅ **Context Middleware** - All API requests now include organization_id, user_id, role
- ✅ **Permission Functions** - `user_has_org_permission()` for role-based access control
- ✅ **Auto User Counting** - Database triggers maintain `current_user_count` automatically
- ✅ **Super Admin Ready** - Architecture prepared for platform-wide admin portal
- 📖 **Documentation** - Complete architecture docs in ORGANIZATION_ARCHITECTURE.md

**Cloud Storage Integration & Brand Compliance! 🎉 (Nov 14, 2025)**
- ✅ **Multi-Cloud Storage Support** - Google Drive, Dropbox, and OneDrive integration
- ✅ **OAuth 2.0 Authentication** - Secure per-user cloud storage connections with token-in-URL pattern for browser redirects
- ✅ **Folder-Level Privacy Controls** - Users can select specific folders to share (e.g., company drive only, not personal files)
  - Database migration: `selected_folders` JSONB column in `user_cloud_storage_tokens` table
  - API endpoints for folder selection and retrieval
  - Privacy filtering enforced in browse endpoints (HTTP 403 if unauthorized path)
- ✅ **Secure Token Revocation** - OAuth tokens properly revoked when disconnecting
  - Google Drive: POST to oauth2.googleapis.com/revoke
  - Dropbox: POST to api.dropboxapi.com/2/auth/token/revoke
  - OneDrive: 1-hour token expiry (no direct revocation API)
- ✅ **Cloud Storage Browse API** - New routes for file/folder browsing
  - GET `/cloud-storage/browse/dropbox` - Browse Dropbox files with privacy filtering
  - GET `/cloud-storage/browse/onedrive` - Browse OneDrive files with privacy filtering
  - GET `/cloud-storage/file/{provider}/{file_id}` - Get temporary download links
  - POST `/cloud-storage/folders/select` - Save folder selections
- ✅ **Media Library Updates** - Dropbox and OneDrive tabs added to Media Library and Social Manager
- ✅ **Brand Guideline Compliance** - Enforced Royal (#1e3a8a), Cobalt (#0047AB), Gold (#FFD700) colors throughout
  - Removed all emojis from Content Calendar and Carousel Maker
  - Updated all cloud storage UI colors from blue to royal/cobalt gradients
  - Fixed button colors in Calendar, Carousel, Social Manager, and Media Library
- ✅ **Environment Variables** - Added DROPBOX_APP_KEY, DROPBOX_APP_SECRET, ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET
- ✅ **Backend Routes** - New files: `cloud_storage_oauth.py`, `cloud_storage_browse.py`
- ✅ **Database Migration** - Migration #006: `add_folder_selection.sql`

**All 8 Platforms Connected! 🎉 (Nov 14, 2025)**
- ✅ **LinkedIn OAuth WORKING** - Migrated to OpenID Connect scopes (openid, profile, email, w_member_social)
- ✅ **Tumblr OAuth WORKING** - OAuth 2.0 publishing enabled
- ✅ **YouTube OAuth WORKING** - Google Cloud OAuth 2.0 with sensitive scopes (youtube, youtube.upload)
- ✅ **Reddit OAuth WORKING** - OAuth 2.0 with identity, submit, and read scopes
- ✅ **WordPress.com OAuth WORKING** - OAuth 2.0 blog publishing
- ⏳ **TikTok IN REVIEW** - OAuth 2.0 configured with correct redirect URI, awaiting approval
- 🎨 **Landing Page Optimized** - Removed repetitive AI infrastructure section, added Pexels API to clean list
- ✨ **Premium Animations** - Implemented cubic-bezier easing [0.22, 1, 0.36, 1], reduced parallax intensity, subtle hover effects
- 🧹 **Code Cleanup** - Deleted 7 backup JSON files (~66KB) from PostgreSQL migration

**Instagram Publishing - WORKING! 🎉 (Nov 13, 2025)**
- ✅ **Instagram OAuth WORKING** - Uses Facebook Login API (instagram_basic, instagram_content_publish, instagram_manage_messages)
- ✅ **Publishing for Business/Creator accounts** - Full end-to-end publishing working
- ✅ **Message management ready** - Can send and receive Instagram messages
- ✅ **Complete OAuth flow** - Connect Instagram → Publish posts → Manage messages
- ✅ **3 Platforms Live** - Twitter ✅ Facebook ✅ Instagram ✅

**Facebook Multi-Tenant Publishing Architecture (Nov 13, 2025)**
- ✅ **Complete Page management system** - Users can select which Facebook Page to post to
- ✅ **GET `/social-auth/facebook/pages`** - Fetches user's managed Facebook Pages with page-specific tokens
- ✅ **POST `/social-auth/facebook/select-page`** - Stores selected page credentials in service_metadata
- ✅ **FacebookPublisher refactored** - Uses per-user OAuth tokens instead of global environment variables
- ✅ **Multi-tenant publishing** - `/publisher/publish` fetches page credentials from service_metadata
- ✅ **Page credentials storage** - service_metadata stores: selected_page_id, selected_page_name, page_access_token
- ✅ **All permissions active** - public_profile, pages_show_list, pages_read_engagement, pages_manage_posts
- ✅ **Publishing enabled** - pages_manage_posts added via "Manage everything on your page" use case
- ✅ **Ready to test** - Facebook OAuth connection and publishing fully configured

**OAuth 2.0 Multi-Tenant Social Publishing (Nov 13, 2025)**
- ✅ **Complete OAuth 2.0 implementation** for all 9 social platforms
- ✅ **Twitter OAuth 2.0 with PKCE** - SHA256 code challenge for security (WORKING + Publishing)
- ✅ **Instagram/Facebook OAuth 2.0** - Unified Meta OAuth system (WORKING with dev permissions)
- ⚠️ **Meta App Review Required** - Advanced permissions (`pages_manage_posts`, `instagram_content_publish`) require Meta app review for publishing functionality
- ✅ **Database schema updates** - 3 migrations (#006, #007, #008) for OAuth support
- ✅ **Per-user social connections** - Users connect their own accounts via settings
- ✅ **Platform redirect URIs** - Configured callback URLs for all platforms
- ✅ **Migration #006** - Added metadata JSONB column to oauth_states table for PKCE
- ✅ **Migration #007** - Added social platforms to connected_services constraint
- ✅ **Migration #008** - Added unique constraint on (user_id, service_type)
- ✅ **Frontend UI** - Social accounts settings page at /dashboard/settings/social-accounts
- ✅ **Backend routes** - `/social-auth/get-auth-url/{platform}`, `/social-auth/callback/{platform}`

**Payment & Credit Management System (Nov 12, 2025)**
- ✅ **Stripe payment integration** with subscription and one-time credit purchases
- ✅ **Credit tracking system** with PostgreSQL functions and audit trail
- ✅ **4 subscription tiers** - Starter (2000 credits), Pro (10000), Business (25000), Enterprise (20000)
- ✅ **4 credit top-up packages** - 500, 1000, 2500, 5000 credits (£125-£650)
- ✅ **Credit deduction** integrated into all AI operations (social captions, images, videos, strategy, competitor analysis)
- ✅ **Real-time credit display** in dashboard header with low balance warnings
- ✅ **Credit purchase modal** with package selection and Stripe checkout
- ✅ **Webhook processing** for automatic credit addition and subscription updates
- ✅ **Usage costs**: Social Caption (2), Blog (5), AI Image (20), AI Video (200), Strategy (10), Competitor Analysis (5)
- ✅ **Rollover limits** by plan: Starter (250), Pro (1000), Business (3000), Enterprise (unlimited)
- ✅ **Email verification gate** - Users must verify email to access paid features
- ✅ **Customer Portal** - Self-service billing management via Stripe

**Brand Asset Management & Cloud Storage (Nov 12, 2025)**
- ✅ **Google Cloud Storage integration** for persistent brand assets (logos, images)
- ✅ **Brand asset extraction** from PDFs (colors, fonts, logos)
- ✅ **OAuth token generators** for Google Drive, OneDrive, Dropbox
- ✅ **Multi-tenant architecture migration** created (ready to apply)
- ✅ Database schema updates for per-user cloud storage tokens
- ✅ Comprehensive environment variable documentation

**Authentication & Multi-User Support (Nov 2025)**
- ✅ JWT-based authentication with bcrypt password hashing
- ✅ User context middleware for per-user data isolation
- ✅ Secure signup/login/refresh endpoints
- ✅ All content scoped to authenticated users

**AI Image & Video Generation (Nov 7, 2025)**
- ✅ Google Imagen 4 Ultra integration for text-to-image generation
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

---

**Last Updated:** November 16, 2025
**Version:** 0.7.0
**Status:** Production-ready with 8/9 social platforms live (TikTok in review), 3-provider cloud storage (Google Drive, Dropbox, OneDrive), organization multi-tenancy with team collaboration, Stripe payments, credit management, OAuth 2.0 architecture, PKCE security, brand guideline compliance, and super admin portal
