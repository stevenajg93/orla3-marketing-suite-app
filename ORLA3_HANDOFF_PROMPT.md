# ORLA³ Marketing Suite - Developer Handoff

## 🚨 FIRST COURSE OF ACTION (November 21, 2025 Code Assessment)

A comprehensive code assessment was conducted on November 21, 2025. The following issues were identified and should be addressed in priority order:

### Phase 1 - Critical Security Fixes (Do First)

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| 1 | **SQL Injection Risk** | `backend/routes/admin.py:177` | Use `psycopg2.sql` module for dynamic WHERE clauses |
| 2 | **JWT Secret Fallback** | `backend/config.py:54` | Remove default value `"your-secret-key-change-in-production-PLEASE"` |
| 3 | **Connection Pool Leaks** | `backend/routes/competitor.py` (7 locations) | Convert to `with get_db_connection() as conn:` pattern |
| 4 | **Error Details Exposed** | 17+ backend routes | Log errors internally, return generic messages to clients |
| 5 | **Bare Except Clauses** | 8 backend files | Replace `except:` with specific exceptions |
| 6 | **Unsafe Redirects** | `lib/api-client.ts`, `app/dashboard/layout.tsx` | Create safe redirect utility with URL validation |

### Phase 2 - High Priority Architectural (Next Sprint)

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| 1 | **Monolithic Component** | `app/dashboard/social/page.tsx` (4,849 lines) | Break into 8-10 smaller components |
| 2 | **No Memoization** | All large frontend components | Add `React.memo()`, `useMemo()`, `useCallback()` |
| 3 | **State Explosion** | 60+ `useState` in single components | Refactor to `useReducer` pattern |
| 4 | **Missing Error Boundaries** | Frontend pages | Add React Error Boundaries |
| 5 | **Token Expiration** | `backend/routes/publisher.py` | Validate OAuth token expiry before API calls |
| 6 | **Request Tracing** | All backend routes | Add request ID middleware for debugging |

### Phase 3 - Medium Priority Quality (Future)

- Replace hardcoded email feature toggles (`s.gillespie@gecslabs.com`) with role-based checks
- Consolidate all API calls to use centralized `api` client (remove raw `fetch()` calls)
- Remove 156 `console.log` statements from frontend
- Add JSDoc comments to public functions
- Implement logging utility to replace console statements
- Add password special character requirement in `utils/auth.py`

### Quick Reference - Connection Pool Fix Pattern
```python
# BEFORE (broken - connection leak):
conn = get_db_connection()
cur = conn.cursor()
# ... queries ...
cur.close()
# Missing: connection never returned to pool!

# AFTER (correct):
with get_db_connection() as conn:
    cur = conn.cursor()
    try:
        # ... queries ...
    finally:
        cur.close()
```

### Quick Reference - Safe Redirect Utility
```typescript
// Create in lib/utils/redirect.ts
const SAFE_PATHS = ['/dashboard', '/login', '/signup', '/admin'];

export function safeRedirect(path: string) {
  if (SAFE_PATHS.some(p => path.startsWith(p))) {
    window.location.href = path;
  } else {
    window.location.href = '/dashboard';
  }
}
```

### Assessment Summary
| Category | Backend | Frontend | Total |
|----------|---------|----------|-------|
| Critical | 6 | 3 | **9** |
| High | 6 | 5 | **11** |
| Medium | 8 | 7 | **15** |
| Low | 5 | 5 | **10** |
| **Total** | **25** | **20** | **45** |

---

## 🎯 PROJECT OVERVIEW

**Orla³ Marketing Suite** is a production-ready, AI-powered marketing automation platform for videographers and creative professionals. Built with clean architecture principles, zero technical debt, and immaculate environment management.

**Live Application:**
- **Frontend**: https://orla3-marketing-suite-app.vercel.app
- **Backend**: https://orla3-marketing-suite-app-production.up.railway.app

---

## 🏗️ ARCHITECTURE

### Core Principles
✅ **Single Source of Truth** - Environment config centralized in `lib/config.ts`
✅ **Zero Hardcoding** - All URLs/endpoints through config system
✅ **Type-Safe API Client** - Centralized HTTP client with error handling
✅ **Environment Aware** - Seamless local/production switching
✅ **Clean Separation** - Frontend (Vercel) + Backend (Railway) + Database (PostgreSQL)

### Tech Stack
```
Frontend:  Next.js 15 + React + TypeScript + Tailwind CSS
Backend:   FastAPI + Python 3.14+ + psycopg2
Database:  PostgreSQL (Railway)
Auth:      JWT tokens + bcrypt password hashing
Payments:  Stripe (subscriptions + credit purchases)
AI:        Multi-provider optimization (8 models)
           - Perplexity AI (real-time web research)
           - Claude Sonnet 4 (strategic/brand-critical)
           - GPT-4o (creative conversational content)
           - Gemini 2.0 Flash (structured visual content)
           - Videographer Smart Search (intelligent content discovery)
           - Imagen 4 Ultra (AI image generation - Vertex AI)
           - Veo 3.1 (AI video generation - Vertex AI)
           - GPT-4o-mini (simple analytical tasks)
Publishing: 9 social platforms (Instagram, LinkedIn, Twitter/X, Facebook,
           TikTok, YouTube, Reddit, Tumblr, WordPress)
Hosting:   Vercel (frontend) + Railway (backend + database)
Node:      v24.10.0, npm 11.6.0
```

---

## 📁 PROJECT STRUCTURE
```
orla3-marketing-suite-app/
├── app/dashboard/              # Next.js app routes
│   ├── blog/                   # SEO blog generator
│   ├── carousel/               # Social media carousel creator
│   ├── social/                 # Social caption generator
│   ├── strategy/               # Brand strategy analyzer
│   ├── competitor/             # Competitor tracking
│   ├── brand-voice/            # Brand voice asset manager
│   ├── calendar/               # Content calendar
│   ├── media/                  # Media library + Drive integration
│   └── library/                # Content library
│
├── lib/                        # Core infrastructure
│   ├── config.ts               # ⭐ Environment configuration
│   ├── api-client.ts           # ⭐ HTTP client (uses config)
│   └── storage.ts              # Local storage utilities
│
├── backend/                    # FastAPI backend
│   ├── routes/                 # API route handlers
│   │   ├── strategy.py         # Brand strategy (PostgreSQL)
│   │   ├── library.py          # Content CRUD (PostgreSQL)
│   │   ├── competitor.py       # Competitor analysis (PostgreSQL)
│   │   ├── brand_voice_upload.py  # Asset uploads (PostgreSQL)
│   │   ├── draft.py            # Blog generation (loads strategy)
│   │   ├── carousel.py         # Carousel generation (loads strategy)
│   │   └── social_caption.py   # Caption generation (loads strategy)
│   ├── main.py                 # FastAPI app + CORS config
│   ├── config.py               # Backend environment config
│   ├── schema.sql              # PostgreSQL schema
│   ├── requirements.txt        # Python dependencies
│   ├── Procfile                # Railway start command
│   └── railway.json            # Railway deployment config
│
├── .env.local                  # Local frontend config (gitignored)
├── backend/.env                # Local backend config (gitignored)
└── README.md                   # Documentation
```

---

## 🗄️ DATABASE SCHEMA

### PostgreSQL Tables

**users** - User accounts, authentication, subscriptions, and credits
```sql
- id, email, password_hash (bcrypt), email_verified
- plan, subscription_status, subscription_started_at, stripe_customer_id
- credit_balance, monthly_credit_allocation, last_credit_reset_at
- total_credits_used, total_credits_purchased
- created_at, updated_at
- JWT tokens for authentication
```

**credit_transactions** - Complete credit audit trail
```sql
- id, user_id (foreign key)
- transaction_type (spent/purchased/allocated/refunded)
- amount, balance_after
- operation_type (social_caption/blog_post/ai_image_ultra/ai_video_8sec/etc)
- operation_details (JSONB), description
- stripe_payment_intent_id, stripe_charge_id
- created_at
```

**brand_strategy** - Single source of brand truth (per user)
```sql
- user_id (foreign key)
- brand_voice (JSONB): tone, personality traits
- messaging_pillars (TEXT[]): core messages
- language_patterns (JSONB): writing style, phrases, vocabulary
- dos_and_donts (JSONB): content guidelines
- competitive_positioning (JSONB): unique value, gaps to exploit
```

**brand_voice_assets** - Uploaded brand materials (per user)
```sql
- user_id (foreign key)
- filename, file_path, category (brand_guideline/example_content/community)
- extracted_text, metadata (JSONB)
- created_at
```

**content_library** - All generated content (per user)
```sql
- user_id (foreign key)
- title, content (JSONB), type (blog/carousel/caption)
- status (draft/published), tags (TEXT[])
- created_at, updated_at
```

**competitors** - Competitor tracking (per user)
```sql
- user_id (foreign key)
- name, website, social_handles (JSONB)
- analysis (JSONB): marketing insights, gaps, opportunities
```

**calendar_events** - Content calendar (per user)
```sql
- user_id (foreign key)
- title, content_id, platform, scheduled_for
- status, notes
```

**oauth_states** - Temporary OAuth state tokens (10-minute TTL)
```sql
- state (TEXT, PRIMARY KEY): CSRF protection token
- user_id (UUID, foreign key): User initiating OAuth
- provider (TEXT): Platform name (instagram, linkedin, twitter, etc.)
- expires_at (TIMESTAMPTZ): 10-minute expiry
- created_at (TIMESTAMPTZ): Timestamp
- metadata (JSONB): Optional data (e.g., PKCE code_verifier for Twitter)
```

**connected_services** - Per-user OAuth tokens
```sql
- user_id (UUID, foreign key): User who connected the service
- service_type (TEXT): Platform name
- service_id (TEXT): Platform-specific user ID
- access_token (TEXT): OAuth access token (encrypted)
- refresh_token (TEXT): OAuth refresh token (encrypted)
- token_expires_at (TIMESTAMPTZ): Token expiration
- service_metadata (JSONB): Platform-specific data
- is_active (BOOLEAN): Connection status
```

---

## 🔧 ENVIRONMENT CONFIGURATION

### Frontend Environment (`.env.local`)
```bash
# Local development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (Vercel env vars)
NEXT_PUBLIC_API_URL=https://orla3-marketing-suite-app-production.up.railway.app
```

### Backend Environment (`backend/.env`)
```bash
# Database (Railway auto-injects DATABASE_URL)
DATABASE_URL=postgresql://postgres:***@switchyard.proxy.rlwy.net:34978/railway

# AI Providers (all 4 required for optimal performance)
ANTHROPIC_API_KEY=sk-ant-***           # Claude Sonnet 4
OPENAI_API_KEY=sk-proj-***             # GPT-4o & GPT-4o-mini
GEMINI_API_KEY=AIza***                 # Gemini 2.0 Flash
PERPLEXITY_API_KEY=pplx-***            # Real-time research

# Media
UNSPLASH_ACCESS_KEY=***

# Google Drive OAuth
GOOGLE_CLIENT_ID=***.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=***
GOOGLE_REDIRECT_URI=https://orla3-marketing-suite-app-production.up.railway.app/drive/callback

# Social Media Publishing (optional - for /publisher endpoints)
INSTAGRAM_ACCESS_TOKEN=***
INSTAGRAM_BUSINESS_ACCOUNT_ID=***
LINKEDIN_ACCESS_TOKEN=***
LINKEDIN_PERSON_URN=urn:li:person:***
TWITTER_API_KEY=***
TWITTER_ACCESS_TOKEN=***
FACEBOOK_PAGE_ACCESS_TOKEN=***
FACEBOOK_PAGE_ID=***
REDDIT_CLIENT_ID=***
REDDIT_CLIENT_SECRET=***
TUMBLR_API_KEY=***
TUMBLR_ACCESS_TOKEN=***
WORDPRESS_SITE_URL=***
WORDPRESS_ACCESS_TOKEN=***
```

---

## 🚀 DEPLOYMENT

### Current Setup
- ✅ **Frontend**: Auto-deploys from `main` branch to Vercel
- ✅ **Backend**: Auto-deploys from `main` branch to Railway
- ✅ **Database**: PostgreSQL managed by Railway
- ✅ **CORS**: Configured to allow both localhost + Vercel

### Deployment Flow
```
1. Push to GitHub main branch
2. Railway builds backend (detects Procfile + requirements.txt)
3. Vercel builds frontend (detects Next.js)
4. Both use respective environment variables
5. CORS allows cross-origin requests
```

---

## 💻 LOCAL DEVELOPMENT

### First-Time Setup

**1. Clone Repository**
```bash
git clone https://github.com/stevenajg93/orla3-marketing-suite-app.git
cd orla3-marketing-suite-app
```

**2. Frontend Setup**
```bash
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev  # Runs on http://localhost:3000
```

**3. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your keys
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY, DATABASE_URL, etc.

python main.py  # Runs on http://localhost:8000
```

### Daily Development Workflow
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend  
npm run dev

# Open: http://localhost:3000
```

---

## 🎨 KEY FEATURES EXPLAINED

### 0. Authentication & Multi-User Support
**Files**: `backend/routes/auth.py`, `backend/middleware/user_context.py`

**Features:**
- JWT-based authentication with bcrypt password hashing
- User context middleware adds `user_id` to all requests
- Per-user data isolation (all content, strategies, competitors scoped to user)
- Secure signup/login/refresh token endpoints

**Endpoints:**
- `POST /auth/signup` - Register new user
- `POST /auth/login` - User login (returns JWT)
- `POST /auth/refresh` - Refresh authentication token

**Security:**
- Passwords hashed with bcrypt before storage
- JWT tokens expire and require refresh
- All database queries filtered by user_id automatically
- No cross-user data leakage

### 0.1. Email Verification System
**Files**: `backend/routes/auth.py`, `backend/utils/email.py`, `app/verify-email/page.tsx`, `app/resend-verification/page.tsx`

**Complete email verification flow with pay-to-access gate:**

**Features:**
- Email verification required before login (HTTP 403 gate)
- Resend API integration for transactional emails
- 7-day verification token expiry
- Beautiful HTML email templates (ORLA³ branded)
- One-click verification from email link
- Resend functionality for expired/lost emails
- Welcome email after successful verification

**Database Fields:**
```sql
users table:
- email_verified (BOOLEAN) - Default false
- verification_token (TEXT) - Unique verification token
- verification_token_expires (TIMESTAMPTZ) - 7-day expiry
```

**Backend Endpoints:**
```
POST /auth/register              # Generates token, sends verification email
POST /auth/verify-email          # Validates token, marks email as verified
POST /auth/resend-verification   # Regenerates token, resends email
POST /auth/login                 # Blocks unverified users (HTTP 403)
```

**Frontend Pages:**
- `/verify-email?token=...` - Auto-verifies from email link, redirects to dashboard
- `/resend-verification` - Manual form to request new verification email
- `UnverifiedEmailBanner` - In-dashboard warning banner with resend button

**Email Templates (Resend):**
1. **Verification Email**: Sent on registration with verification link
2. **Welcome Email**: Sent after successful verification
3. **Password Reset Email**: For password recovery flow

**Environment Variables:**
```bash
RESEND_API_KEY=re_...           # Resend API key for email sending
FROM_EMAIL=noreply@orla3.com    # Sender email address
FRONTEND_URL=https://...         # For verification links
```

**Two-Gate Access Model:**
1. **Email Verification Gate** (HTTP 403) - First barrier
   - User registers → receives verification email
   - Must click link to verify
   - Cannot login until verified

2. **Payment Gate** (HTTP 402) - Second barrier
   - Even after email verification, must have active paid subscription
   - Blocks free plans and inactive subscriptions
   - Redirects to Stripe checkout

**Security:**
- Tokens are single-use (cleared after verification)
- 7-day expiry automatically enforced
- Secure token generation with secrets module
- Graceful handling if Resend not configured (logs warning)

### 1. Payment & Credit Management System
**Files**: `backend/routes/payment.py`, `backend/routes/credits.py`, `backend/utils/credits.py`

**Complete Stripe integration with credit-based usage system:**

**Subscription Plans:**
- **Starter** (£25/month): 2000 credits/month, 250 rollover limit
- **Professional** (£75/month): 10,000 credits/month, 1000 rollover limit
- **Business** (£150/month): 25,000 credits/month, 3000 rollover limit
- **Enterprise** (£300/month): 20,000 credits/month, unlimited rollover

**Credit Top-Up Packages** (one-time purchases):
- 500 credits: £125 (£0.25/credit)
- 1000 credits: £200 (£0.20/credit)
- 2500 credits: £400 (£0.16/credit)
- 5000 credits: £650 (£0.13/credit)

**Credit Costs:**
- Social Caption: 2 credits
- Blog Post: 5 credits
- AI Image (Imagen 4 Ultra): 20 credits
- AI Video (Veo 3.1 - 8sec): 200 credits
- Strategy Generation: 10 credits
- Competitor Analysis: 5 credits
- Brand Voice Analysis: 3 credits

**Key Features:**
- Pre-flight credit checking (prevents failed operations)
- Atomic deduction via PostgreSQL functions
- Complete transaction audit trail
- HTTP 402 response when insufficient credits
- Real-time balance updates in frontend
- Webhook processing for purchases
- Email verification gate (pay-to-access model)
- Stripe Customer Portal for billing management

**Payment Endpoints:**
```
POST   /payment/create-checkout         # Create subscription checkout
POST   /payment/purchase-credits        # Create credit top-up checkout
POST   /payment/webhook                 # Stripe webhook handler
POST   /payment/create-portal-session   # Customer Portal access
GET    /payment/subscription            # Get user subscription
GET    /payment/credit-packages         # Get available credit packages
```

**Credit Endpoints:**
```
GET    /credits/balance                 # Get current credit balance
GET    /credits/history                 # Get transaction history
GET    /credits/costs                   # Get operation costs
GET    /credits/check/{operation_type}  # Check if user has enough credits
```

**Frontend Components:**
- `lib/hooks/useCredits.ts` - React hook for credit management
- `components/CreditPurchaseModal.tsx` - Credit purchase UI
- Dashboard header credit display with low balance warnings

**Credit Deduction Integration:**
All AI endpoints check credits before processing:
- `routes/social_caption.py` - `/generate-caption`
- `routes/ai_generation.py` - `/generate-image`, `/generate-video-veo`
- `routes/strategy.py` - `/analyze`
- `routes/competitor.py` - `/{id}/analyze`

### 2. Brand Strategy Intelligence
**File**: `backend/routes/strategy.py`

Upload brand materials → AI analyzes (Claude Sonnet 4) → Generates comprehensive strategy:
- Brand voice (tone, personality)
- Messaging pillars
- Language patterns (phrases, vocabulary)
- Competitive positioning (unique value, gaps)

This strategy is **automatically applied** to all content generation.

**AI Model Selection:**
- Brand analysis: Claude Sonnet 4 (strategic depth required)
- Next keyword: GPT-4o-mini (simple recommendation)
- Market research: GPT-4o-mini (analytical task)

### 2. Content Generation Suite

**Blog Writer** (`backend/routes/draft.py`) - Claude Sonnet 4
- Auto-selects keywords from strategy
- Researches market with web search
- Generates SEO-optimized, brand-aligned articles
- Long-form, premium quality required

**Carousel Creator** (`backend/routes/carousel.py`) - Gemini 2.0 Flash
- 7-slide Instagram/LinkedIn carousels
- Applies brand voice throughout
- Fetches Unsplash images automatically
- Structured output optimized for speed

**Social Captions** (`backend/routes/social_caption.py`) - GPT-4o
- Platform-aware (Twitter, Instagram, LinkedIn, Facebook)
- Includes brand-aligned hashtags
- Respects character limits
- Conversational, empathetic tone

**Trend Research** (`backend/routes/social_caption.py`) - Perplexity AI
- Real-time social media trend analysis
- Current trending hashtags and topics
- Industry-specific insights

**Blog Atomization** (`backend/routes/atomize.py`) - Gemini 2.0 Flash
- Converts blog posts to 8 platform-specific posts
- Platform-optimized formatting (LinkedIn, Twitter, Facebook, Instagram, TikTok, YouTube, Reddit, Tumblr)
- Maintains brand voice across all platforms

**Ad Copy Generator** (`backend/routes/ads.py`) - GPT-4o
- Multi-platform ad campaigns (Meta, LinkedIn, Twitter/X)
- Creative headlines and persuasive copy
- Targeting suggestions included

**Comment Replies** (`backend/routes/comments.py`) - GPT-4o
- AI-powered engagement responses
- Empathetic, brand-aligned tone
- Priority and sentiment analysis

### 3. Competitive Intelligence
**File**: `backend/routes/competitor.py`

**Two-Stage AI Process:**
1. **Research Phase** (Perplexity AI)
   - Real-time web scraping of competitor marketing content
   - Analyzes social media posts, website copy, messaging
   - Gathers actual examples of their content strategies

2. **Analysis Phase** (Claude Sonnet 4)
   - Strategic analysis through Orla³'s brand lens
   - Identifies content gaps to exploit
   - Evaluates market-based threat level (direct/indirect/minimal)
   - Provides positioning recommendations

**Key Features:**
- Track competitors by name/social handles
- Automated research with live web data
- Market-based threat assessment (not just marketing similarity)
- Feeds into brand strategy automatically

### 4. Media Management & Cloud Storage
**Files**: `backend/routes/media.py`, `backend/routes/ai_generation.py`, `backend/routes/cloud_storage_oauth.py`, `backend/routes/cloud_storage_browse.py`

**Multi-Cloud Storage Integration:**
- ✅ **3 Cloud Providers**: Google Drive, Dropbox, OneDrive
- ✅ **OAuth 2.0 Per-User Authentication**: Secure cloud storage connections with token-in-URL pattern for browser redirects
- ✅ **Folder-Level Privacy Controls**: Users can limit access to specific folders (e.g., company drive only, not personal files)
  - Database: `selected_folders` JSONB column in `user_cloud_storage_tokens` table
  - API: POST `/cloud-storage/folders/select`, GET `/cloud-storage/folders/selected`
  - Enforcement: Privacy filtering in browse endpoints (HTTP 403 if unauthorized path)
- ✅ **Secure Token Revocation**: OAuth tokens properly revoked on disconnect
  - Google Drive: POST to `oauth2.googleapis.com/revoke`
  - Dropbox: POST to `api.dropboxapi.com/2/auth/token/revoke`
  - OneDrive: 1-hour token expiry (no direct revocation API)
- ✅ **File Browsing & Import**: Browse files/folders from all connected providers
  - GET `/cloud-storage/browse/dropbox` - Browse Dropbox with privacy filtering
  - GET `/cloud-storage/browse/onedrive` - Browse OneDrive with privacy filtering
  - GET `/cloud-storage/file/{provider}/{file_id}` - Get temporary download links
- ✅ **UI Integration**: Cloud storage tabs in Media Library (`app/dashboard/media/page.tsx`) and Social Manager (`app/dashboard/social/page.tsx`)

**Database Schema:**
```sql
user_cloud_storage_tokens table:
- user_id, provider (google_drive/dropbox/onedrive)
- access_token, refresh_token, token_expires_at
- selected_folders (JSONB) - Array of folder IDs/paths user granted access to
- is_active, created_at, updated_at
```

**AI Generation:**
- **AI Image Generation** (Google Imagen 4 Ultra)
  - Text-to-image with aspect ratio options (1:1, 16:9, 9:16, 4:3, 3:4)
  - $0.03 per image
  - Gallery view with download/preview
- **AI Video Generation**
  - **Google Veo 3.1**: Text-to-video with resolution options (720p, 1080p), $6 per 8s video with audio
  - Async generation (2-5 minutes)
  - Status tracking via job ID
- Unified content library with filtering
- Tag-based organization

### 5. Social Media Publishing & Engagement
**Files**: `backend/routes/social_auth.py`, `backend/routes/publisher.py`, `backend/routes/comments.py`

**OAuth 2.0 Multi-Tenant Architecture:**
- ✅ **All 9 Platforms**: Instagram, LinkedIn, Twitter/X, Facebook, TikTok, YouTube, Reddit, Tumblr, WordPress
- ✅ **Per-User Connections**: Users connect their own accounts via `/dashboard/settings/social-accounts`
- ✅ **Secure Token Storage**: OAuth tokens stored encrypted in `connected_services` table
- ✅ **PKCE Security**: Twitter OAuth 2.0 uses SHA256 code challenge (stored in `oauth_states.metadata`)
- ✅ **CSRF Protection**: State tokens with 10-minute expiry in `oauth_states` table

**Engagement Features:**
- ✅ **AI Comment Replies**: Automatically generate brand-aligned responses to comments (`backend/routes/comments.py`)
- ✅ **Social Discovery**: Search non-follower posts by keywords and trends to engage with relevant conversations
- ✅ **Trends Search**: Real-time trending topics discovery to inform content strategy and engagement timing
- Uses platform APIs to search, analyze sentiment, and suggest engagement opportunities

**Platform Status:**
- ✅ **Twitter/X**: Full OAuth 2.0 with PKCE working (tweets can be published) ✅ WORKING
- ✅ **Facebook**: Complete multi-tenant architecture with Page management + publishing ✅ WORKING
  - Users can list their managed Pages (working)
  - Users can select which Page to post to (working)
  - Users can publish posts to selected Page (working)
  - Page credentials (page_access_token, selected_page_id) stored in service_metadata
  - Active permissions: `public_profile`, `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
  - Added via "Manage everything on your page" use case in Meta console
- ✅ **Instagram**: Full OAuth 2.0 + publishing for Business/Creator accounts ✅ WORKING
  - Uses Facebook Login API (NOT separate Instagram app)
  - Active permissions: `public_profile`, `pages_show_list`, `pages_read_engagement`, `business_management`, `instagram_basic`, `instagram_content_publish`, `instagram_manage_messages`
  - Requires Instagram Business or Creator account (not personal account)
  - Can publish posts and manage messages
  - Uses Facebook app credentials (App ID: 3637140849749643)
  - Permissions from "API setup with Facebook login" in Meta console
- ✅ **LinkedIn**: OpenID Connect OAuth 2.0 + publishing ✅ WORKING
  - Migrated scopes: `openid`, `profile`, `email`, `w_member_social`
  - Replaces deprecated `r_liteprofile` and `r_emailaddress`
  - Company page verification completed
  - Redirect URI: `https://orla3-marketing-suite-app-production.up.railway.app/social-auth/callback/linkedin`
- ✅ **Tumblr**: OAuth 2.0 + publishing ✅ WORKING
  - OAuth 2.0 (modern version, not OAuth 1.0a)
  - Scopes: `basic`, `write`
  - Redirect URI: `https://orla3-marketing-suite-app-production.up.railway.app/social-auth/callback/tumblr`
- ⏳ **YouTube**: Google OAuth 2.0 configured ⏳ VERIFICATION PENDING
  - Web application OAuth client (not Desktop type)
  - Sensitive scopes: `https://www.googleapis.com/auth/youtube`, `https://www.googleapis.com/auth/youtube.upload`
  - Client ID: `[REDACTED - See Railway environment variables]`
  - Redirect URI: `https://orla3-marketing-suite-app-production.up.railway.app/social-auth/callback/youtube`
  - **Verification Status**: Awaiting Google OAuth verification approval (homepage verification in progress)
- ✅ **Reddit**: OAuth 2.0 + post submission ✅ WORKING
  - Scopes: `identity`, `submit`, `read`
  - 1-hour token expiration (normal, handled by refresh tokens)
  - Redirect URI: `https://orla3-marketing-suite-app-production.up.railway.app/social-auth/callback/reddit`
- ✅ **WordPress.com**: OAuth 2.0 + blog publishing ✅ WORKING
  - Scopes: `posts`
  - Client ID: `127672`
  - Redirect URI: `https://orla3-marketing-suite-app-production.up.railway.app/social-auth/callback/wordpress`
- ⏳ **TikTok**: OAuth 2.0 configured, awaiting app approval (1-3 days) ⏳ IN REVIEW
  - Redirect URI corrected to backend: `https://orla3-marketing-suite-app-production.up.railway.app/social-auth/callback/tiktok`
  - Resubmitted for review after fixing redirect URI
  - Client Key: `awpnl0i94s21sv96`

**🎉 7/9 PLATFORMS LIVE: Twitter ✅ | Facebook ✅ | Instagram ✅ | LinkedIn ✅ | Tumblr ✅ | YouTube ⏳ | Reddit ✅ | WordPress.com ✅ | TikTok ⏳**

**OAuth 2.0 Endpoints:**
- `GET /social-auth/get-auth-url/{platform}` - Get OAuth URL (requires JWT auth)
- `GET /social-auth/callback/{platform}` - Handle OAuth callback
- `GET /social-auth/status` - Check connected platforms for user
- `POST /social-auth/disconnect/{platform}` - Disconnect platform
- `GET /social-auth/facebook/pages` - Get user's Facebook Pages (requires JWT auth)
- `POST /social-auth/facebook/select-page` - Select Facebook Page for publishing (requires JWT auth)

**Publishing Endpoints:**
- `POST /publisher/publish` - Universal publishing API (multi-tenant, uses per-user credentials)
- `GET /publisher/status` - Check user's connected platforms
- `GET /publisher/status-all` - Platform status checking (legacy)

**Platform-Specific OAuth Setup:**
Each platform requires whitelisting redirect URI in developer console:
```
https://orla3-marketing-suite-app-production.up.railway.app/social-auth/callback/{platform}
```

**Important Notes:**
- **Instagram uses Facebook's OAuth system** - Both share the same callback URL (`/callback/facebook`)
- Instagram redirect URI should NOT be added separately to Meta Developer Console
- Twitter requires PKCE (code_verifier stored in `oauth_states.metadata` JSONB column)
- Twitter OAuth 2.0 uses Basic Authorization header (not request body credentials)
- **Facebook Page Management** - Users must select a Facebook Page before publishing
  - Page list fetched from `/me/accounts` endpoint
  - Each page has its own page_access_token (more secure than user access token)
  - Selected page credentials stored in connected_services.service_metadata
  - FacebookPublisher class now requires page_access_token and page_id parameters

**Database Tables:**
- `oauth_states` - Temporary state tokens for CSRF protection (10min TTL), includes metadata for PKCE
- `connected_services` - Per-user OAuth tokens and refresh tokens, service_metadata stores platform-specific config (e.g., Facebook Page selection)

---

## 📊 API ENDPOINTS

### Authentication
```
POST   /auth/signup                # Register new user
POST   /auth/login                 # User login (returns JWT)
POST   /auth/refresh               # Refresh authentication token
```

### Strategy
```
POST   /strategy/analyze          # Generate brand strategy (user-scoped)
GET    /strategy/current           # Get current strategy (user-scoped)
POST   /strategy/market-research   # Keyword research
GET    /strategy/next-keyword      # Auto-select next keyword
```

### Content Generation
```
POST   /draft/content/draft        # Generate blog post
POST   /carousel/social/carousel   # Generate carousel
POST   /social-caption/generate-caption  # Generate caption
```

### Library
```
GET    /library/content            # List all content
POST   /library/content            # Save content
PUT    /library/content/{id}       # Update content
DELETE /library/content/{id}       # Delete content
```

### Competitors
```
GET    /competitor/list            # List competitors
POST   /competitor/add             # Add competitor
POST   /competitor/{id}/analyze    # Analyze competitor
DELETE /competitor/{id}            # Delete competitor
GET    /competitor/insights        # Get insights
```

### Brand Voice
```
GET    /brand-voice/assets         # List uploaded assets
POST   /brand-voice/upload         # Upload new asset
POST   /brand-voice/import-from-drive  # Import from Drive
DELETE /brand-voice/assets/{id}   # Delete asset
```

### AI Generation
```
POST   /ai/generate-image          # Generate image (Imagen 4 Ultra)
POST   /ai/generate-video          # Generate video (Veo 3.1)
GET    /ai/video-status/{job_id}   # Check video generation status
```

### Cloud Storage
```
# OAuth 2.0 Authentication
GET    /cloud-storage/connect/google_drive     # Initiate Google Drive OAuth
GET    /cloud-storage/connect/dropbox          # Initiate Dropbox OAuth
GET    /cloud-storage/connect/onedrive         # Initiate OneDrive OAuth
GET    /cloud-storage/callback/{provider}      # OAuth callback handler
DELETE /cloud-storage/disconnect/{provider}    # Disconnect and revoke tokens
GET    /cloud-storage/connections              # Get user's connected providers

# File Browsing
GET    /cloud-storage/browse/dropbox           # Browse Dropbox files (with privacy filtering)
GET    /cloud-storage/browse/onedrive          # Browse OneDrive files (with privacy filtering)
GET    /cloud-storage/file/{provider}/{file_id} # Get temporary download link

# Folder Privacy Controls
POST   /cloud-storage/folders/select           # Save folder selection preferences
GET    /cloud-storage/folders/selected         # Get selected folders
```

---

## 🔒 SECURITY & BEST PRACTICES

### Security Posture ✅
- **Zero hardcoded credentials** - All secrets use `os.getenv()` with validation
- **Environment templates** - `.env.example` files for both frontend and backend
- **Git protection** - Comprehensive `.gitignore` prevents credential commits
- **Type safety** - TypeScript type guards prevent runtime errors
- **Error handling** - All catch blocks log errors for debugging
- **CORS protection** - Restricted to verified origins only

### Recent Updates (Nov 2025)

**0. Cloud Storage Integration & Brand Compliance! 🎉 (Nov 14, 2025)**
- ✅ **Multi-Cloud Storage Support** - Integrated Google Drive, Dropbox, and OneDrive
  - OAuth 2.0 per-user authentication with token-in-URL pattern for browser redirects
  - New backend routes: `cloud_storage_oauth.py` (OAuth flows), `cloud_storage_browse.py` (file browsing)
  - Database migration #006: Added `selected_folders` JSONB column to `user_cloud_storage_tokens`

- ✅ **Folder-Level Privacy Controls** - Users can select specific folders to share
  - Database: `selected_folders` JSONB array stores allowed folder IDs/paths
  - API endpoints: POST `/cloud-storage/folders/select`, GET `/cloud-storage/folders/selected`
  - Privacy enforcement: Browse endpoints return HTTP 403 if accessing unauthorized paths
  - Use case: Share company drive folder only, keep personal files private

- ✅ **Secure Token Revocation** - OAuth tokens properly revoked on disconnect
  - Google Drive: POST to `oauth2.googleapis.com/revoke` with access_token
  - Dropbox: POST to `api.dropboxapi.com/2/auth/token/revoke` with Bearer token
  - OneDrive: Automatic 1-hour token expiry (no direct revocation API)

- ✅ **Cloud Storage Browse API** - File/folder browsing with privacy filtering
  - GET `/cloud-storage/browse/dropbox?path={path}` - Dropbox files with folder privacy
  - GET `/cloud-storage/browse/onedrive?path={path}` - OneDrive files with folder privacy
  - GET `/cloud-storage/file/{provider}/{file_id}` - Temporary download links
  - Supports pagination and breadcrumb navigation

- ✅ **UI Integration** - Cloud storage tabs in Media Library and Social Manager
  - `app/dashboard/media/page.tsx` - Standalone Media Library with Dropbox/OneDrive tabs
  - `app/dashboard/social/page.tsx` - Social Manager media modal with cloud storage options
  - `app/dashboard/settings/cloud-storage/page.tsx` - Cloud storage connection management

- ✅ **Brand Guideline Compliance** - Enforced Royal, Cobalt, Gold color palette
  - Removed ALL emojis from Content Calendar and Carousel Maker
  - Updated cloud storage UI from blue gradients to royal/cobalt brand colors
  - Fixed button colors across Calendar, Carousel, Social Manager, and Media Library
  - Files updated: `calendar/page.tsx`, `carousel/page.tsx`, `social/page.tsx`, `media/page.tsx`

- ✅ **Google Drive OAuth Fix** - Updated to web application OAuth client
  - Changed from desktop client to web application client
  - Client ID: `[REDACTED - See Railway environment variables]`
  - Client Secret: `[REDACTED - See Railway environment variables]`
  - Redirect URI properly configured: `{BACKEND_URL}/cloud-storage/callback/google_drive`

- ✅ **Environment Variables** - Added cloud storage OAuth credentials
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (web application client)
  - `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`
  - `ONEDRIVE_CLIENT_ID`, `ONEDRIVE_CLIENT_SECRET`

**0. All 8 Platforms Connected! 🎉 (Nov 14, 2025)**
- ✅ **LinkedIn OAuth WORKING** - Migrated to OpenID Connect scopes (openid, profile, email, w_member_social)
  - Updated `backend/routes/social_auth.py` lines 73-84 with new scopes
  - Replaces deprecated `r_liteprofile` and `r_emailaddress`
  - Company page verification completed
- ✅ **Tumblr OAuth WORKING** - OAuth 2.0 publishing enabled
  - Clarified OAuth 2.0 vs 1.0a (using OAuth 2.0)
  - Both callback fields configured in Tumblr app settings
- ✅ **YouTube OAuth WORKING** - Google Cloud OAuth 2.0 with sensitive scopes (youtube, youtube.upload)
  - Created new "Web application" OAuth client (replaced Desktop client)
  - Added YouTube scopes in "Data access" tab of Google Cloud Console
  - New credentials: Client ID `[REDACTED - See Railway environment variables]`
- ✅ **Reddit OAuth WORKING** - OAuth 2.0 with identity, submit, and read scopes
  - 1-hour token expiration handled by refresh tokens
  - Permissions: Access posts/comments, submit links/comments, access username
- ✅ **WordPress.com OAuth WORKING** - OAuth 2.0 blog publishing
  - Client ID: `127672`
  - Scopes: `posts`
- ⏳ **TikTok IN REVIEW** - OAuth 2.0 configured with correct redirect URI, awaiting approval
  - Fixed redirect URI from frontend (`https://orla3.com`) to backend Railway URL
  - Withdrew and resubmitted app for review
  - Expected approval: 1-3 business days
- 🎨 **Landing Page Optimized**
  - Removed repetitive "Built on World-Class AI Infrastructure" section with tiles
  - Replaced with clean badge list of AI models and APIs
  - Added Pexels API to list (stock video provider)
  - File: `app/page.tsx` lines 202-224
- ✨ **Premium Animations**
  - Implemented cubic-bezier easing [0.22, 1, 0.36, 1] across all animations
  - Reduced parallax intensity (50% → 20%)
  - Changed viewport triggers (-100px → -50px)
  - Replaced aggressive scale hovers (1.05) with subtle vertical lifts (-4px/-8px)
  - Made all hover states consistent (300ms duration, ease-out)
  - File: `app/page.tsx` throughout
- 🧹 **Code Cleanup**
  - Deleted 7 backup JSON files (~66KB) from PostgreSQL migration
  - Files: `backend/routes/*_json_backup.py`

**0. OAuth 2.0 Multi-Tenant Social Publishing (Nov 13, 2025)**
- ✅ **Complete OAuth 2.0 implementation** for all 9 social platforms
  - Instagram, LinkedIn, Twitter/X, Facebook, TikTok, YouTube, Reddit, Tumblr, WordPress
  - Per-user account connections via /dashboard/settings/social-accounts
  - Secure token storage in `connected_services` table

- ✅ **Twitter OAuth 2.0 with PKCE** (fully working)
  - SHA256 code challenge/verifier implementation
  - PKCE code_verifier stored in `oauth_states.metadata` (JSONB column)
  - Proper OAuth 2.0 flow with state token CSRF protection
  - Basic Authorization header for token exchange (OAuth 2.0 spec compliant)
  - Migration #006: Added metadata column to oauth_states table
  - Migration #007: Added social platforms to connected_services constraint
  - Migration #008: Added unique constraint on (user_id, service_type)

- ✅ **Facebook Multi-Tenant Publishing Architecture** (Nov 13, 2025) - COMPLETE & WORKING
  - GET /social-auth/facebook/pages - Fetches user's managed Facebook Pages (working)
  - POST /social-auth/facebook/select-page - Stores selected page credentials (working)
  - FacebookPublisher refactored to use per-user OAuth tokens (page_access_token, page_id)
  - Page credentials stored in connected_services.service_metadata (JSONB)
  - /publisher/publish endpoint retrieves page credentials from service_metadata per-user
  - Facebook permissions: `public_profile`, `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
  - ✅ **Publishing enabled**: pages_manage_posts added via "Manage everything on your page" use case
  - End-to-end flow working: OAuth → List Pages → Select Page → Publish Post

- ✅ **Instagram Publishing - WORKING!** (Nov 13, 2025) 🎉
  - Instagram uses Facebook's OAuth system (unified Meta platform)
  - Uses Facebook app credentials (NOT separate Instagram app)
  - Both Instagram and Facebook share same callback URL: `/callback/facebook`
  - Instagram permissions: `public_profile`, `pages_show_list`, `pages_read_engagement`, `business_management`, `instagram_basic`, `instagram_content_publish`, `instagram_manage_messages`
  - Permissions from "API setup with Facebook login" (NOT instagram_business_* versions)
  - Requires Instagram Business or Creator account (not personal account)
  - End-to-end flow working: OAuth → Publish posts → Manage messages
  - **Key Learning**: Use regular instagram_* permissions (activated), not instagram_business_* (not activated)

- ✅ **OAuth flow implementation**
  - Two-step flow: Frontend calls `/get-auth-url/{platform}` with JWT
  - Backend generates state token and PKCE challenge (Twitter only)
  - User redirects to platform for authorization
  - Callback exchanges code for access/refresh tokens
  - Tokens stored per-user in database with ON CONFLICT upsert

- ✅ **Frontend social accounts page**
  - OAuth connection UI for all 9 platforms
  - Platform-specific logos and branding (Instagram gradient, X logo, etc.)
  - Connection status display
  - Disconnect functionality

- ✅ **Backend routes** (`backend/routes/social_auth.py` - 505 lines)
  - GET /social-auth/get-auth-url/{platform} - Initiate OAuth (JWT required)
  - GET /social-auth/callback/{platform} - Handle OAuth callback
  - GET /social-auth/status - Check user's connected platforms
  - POST /social-auth/disconnect/{platform} - Remove platform connection
  - Platform configurations for all 9 services (auth URLs, token URLs, scopes)

**0. Payment & Credit Management System (Nov 12, 2025)**
- ✅ **Complete Stripe integration**
  - Subscription checkout with 4 tier plans (Starter, Professional, Business, Enterprise)
  - Credit top-up packages (500, 1000, 2500, 5000 credits at £125-£650)
  - Webhook processing for automatic credit allocation and subscription updates
  - Stripe Customer Portal for self-service billing management

- ✅ **Credit tracking and enforcement**
  - PostgreSQL credit_transactions table with complete audit trail
  - Database functions: record_credit_transaction(), has_sufficient_credits(), reset_monthly_credits()
  - Credit columns in users table: credit_balance, monthly_credit_allocation, total_credits_used, total_credits_purchased
  - Rollover limits by plan: Starter (250), Professional (1000), Business (3000), Enterprise (unlimited)

- ✅ **Credit deduction integration**
  - All AI operations deduct credits BEFORE processing
  - HTTP 402 response with detailed error when insufficient credits
  - Operation costs: Social Caption (2), Blog (5), AI Image (20), AI Video (200), Strategy (10), Competitor (5)
  - Integrated into: social_caption.py, ai_generation.py, strategy.py, competitor.py

- ✅ **Frontend credit management**
  - Real-time credit balance in dashboard header with low balance warnings (yellow < 20%)
  - Credit purchase modal with 4 package options and pricing details
  - React hook (useCredits.ts) for state management
  - Monthly allocation and usage percentage display

- ✅ **Pay-to-access model**
  - Email verification gate - users must verify email to use platform
  - Subscription required for all AI operations
  - Credit system prevents overuse and enforces limits

**0. Brand Asset Management & Cloud Storage (Nov 12, 2025)**
- ✅ **Google Cloud Storage (GCS) integration**
  - Persistent storage for brand logos and images
  - Bucket auto-creation with public access
  - OAuth2 authentication with refresh tokens
  - Railway ephemeral filesystem → GCS (logos survive redeploys)

- ✅ **Brand asset extraction from PDFs**
  - Automatic color extraction (hex, RGB formats)
  - Font family detection from brand guidelines
  - Logo discovery from uploaded files (GCS or local)
  - Stored in PostgreSQL brand_strategy table

- ✅ **OAuth token generators** for multi-cloud support
  - `get_google_drive_token.py` - Google Drive OAuth2
  - `get_onedrive_token.py` - Microsoft OneDrive OAuth2
  - `get_dropbox_token.py` - Dropbox OAuth2
  - Each opens browser, handles OAuth flow, returns refresh token

- ✅ **Multi-tenant architecture migration** (prepared, not applied yet)
  - New tables: users, user_cloud_storage_tokens, refresh_tokens, audit_log
  - Added user_id foreign keys to all content tables
  - Per-user OAuth tokens (encrypted in database)
  - System admin role (no billing for s.gillespie@gecslabs.com)
  - See: `backend/migrations/001_add_multi_tenant_architecture.sql`

- ✅ **Comprehensive documentation**
  - `backend/MULTI_TENANT_ARCHITECTURE_PLAN.md` - Full refactor plan
  - `backend/RAILWAY_ENVIRONMENT_VARIABLES.md` - Production setup guide
  - Updated `.env.example` with all cloud storage variables

**1. Authentication & Multi-User Support (Nov 2025)**
- ✅ **JWT-based authentication**
  - Bcrypt password hashing
  - Secure signup/login/refresh endpoints
  - User context middleware for automatic user_id injection

- ✅ **Per-user data isolation**
  - All content scoped to authenticated user
  - Separate brand strategies per user
  - Individual competitor tracking
  - Personal content libraries

- ✅ **Database updates**
  - Added `users` table with authentication fields
  - All tables include user_id foreign keys
  - Automatic filtering by user context

**1. AI Image & Video Generation (Nov 7, 2025)**
- ✅ **Google Imagen 4 Ultra integration**
  - Text-to-image generation
  - 5 aspect ratio options (1:1, 16:9, 9:16, 4:3, 3:4)
  - Integrated into Media Library and Social Manager
  - Gallery view with download/preview buttons

- ✅ **AI Video Generation**
  - **Google Veo 3.1**: $6 per 8s video with native audio
  - 720p HD and 1080p Full HD options
  - Async generation with status tracking
  - 2-5 minute generation time

- ✅ **New backend route**: `backend/routes/ai_generation.py`
  - POST /ai/generate-image
  - POST /ai/generate-video
  - GET /ai/video-status/{job_id}

- ✅ **Frontend updates**
  - Added AI tabs to Media Library page
  - Added AI tabs to Social Manager media modal
  - State management for prompts and generated content
  - Download and preview functionality

**2. AI Model Optimization (Nov 7, 2025)**
- ✅ **Multi-provider strategy** for 60-75% cost reduction
  - OpenAI GPT-4o: Creative conversational content (captions, comments, ads)
  - Gemini 2.0 Flash: Structured visual content (carousels, atomization)
  - GPT-4o-mini: Simple analytical tasks (15x cheaper than Sonnet 4)
  - Claude Sonnet 4: Strategic/brand-critical only (competitor analysis, brand strategy, blogs)
  - Perplexity AI: Real-time web research (competitor content, trends)

- ✅ **Dependencies added**:
  - `openai==1.54.3`
  - `google-generativeai==0.8.3`

- ✅ **11 route files updated** with optimal model selection

**2. Competitor Analysis Enhancement (Nov 7, 2025)**
- ✅ **Fixed threat level assessment**
  - Now evaluates market competition (same customers/service)
  - Previously only evaluated marketing similarity
  - Direct competitors correctly identified regardless of tactics

- ✅ **Automated research with Perplexity AI**
  - Real-time scraping of competitor marketing content
  - Analyzes actual social posts, website copy
  - Feeds into Claude Sonnet 4 for strategic analysis

**3. Social Media Integration (Nov 7, 2025)**
- ✅ **9-platform publishing infrastructure**
  - Instagram, LinkedIn, Twitter/X, Facebook, TikTok, YouTube, Reddit, Tumblr, WordPress
  - Universal publishing API endpoint
  - Platform status checking
  - Twitter/X and WordPress fully functional

**4. Security Fixes (Nov 6, 2025)**
- ✅ **Removed exposed credentials from git**
  - Removed 4 Google OAuth credential files from git history
  - Removed hardcoded DATABASE_URL from 13 backend files
  - Updated `.gitignore` with explicit patterns

- ✅ **Implemented secure environment pattern**
  - Changed from: `DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://...")`
  - Changed to: `DATABASE_URL = os.getenv("DATABASE_URL")` with validation
  - Created comprehensive `.env.example` templates
  - Added SETUP.md with security best practices

- ✅ **Code quality improvements**
  - Fixed 8 TypeScript ContentBlock type errors
  - Replaced 9 'any' types with proper type definitions
  - Added error logging to 12 catch blocks
  - Removed 6 duplicate backend files

### Environment Variables
- ✅ Never commit `.env` or `.env.local` files
- ✅ All secrets in environment variables only
- ✅ Railway auto-manages DATABASE_URL (injected at runtime)
- ✅ Vercel securely stores NEXT_PUBLIC_API_URL
- ✅ Use `.env.example` templates for setup

### CORS Configuration
**File**: `backend/main.py`
```python
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://orla3-marketing-suite-app.vercel.app",  # Production
]
```

### Database Migrations
- Schema defined in `backend/schema.sql`
- Use PostgreSQL client to apply updates
- Always backup before schema changes
- DATABASE_URL never hardcoded - always from environment

---

## 🐛 COMMON ISSUES & SOLUTIONS

### Production Health Status ✅
**Last Verified**: November 6, 2025

All production endpoints verified working:
```bash
✅ GET  / → 200 OK (FastAPI root)
✅ GET  /health → 200 OK
✅ GET  /strategy/current → 200 OK
✅ GET  /library/content → 200 OK
✅ GET  /competitor/list → 200 OK
```

**Quick Health Check**:
```bash
# Check production backend
curl https://orla3-marketing-suite-app-production.up.railway.app/health

# Check local backend
curl http://localhost:8000/health
```

### Issue: "Failed to auto-generate. Make sure backend is running."
**Solution**: Check if backend is running on correct URL
```bash
# Check local backend
curl http://localhost:8000/

# Check production backend
curl https://orla3-marketing-suite-app-production.up.railway.app/
```

### Issue: CORS errors in browser console
**Solution**: Verify `allowed_origins` in `backend/main.py` includes your frontend URL

### Issue: Environment variables not loading
**Solution**: Restart dev servers after changing `.env` files
```bash
# Kill both terminals (Ctrl+C)
# Restart backend: python main.py
# Restart frontend: npm run dev
```

### Issue: Database connection errors
**Solution**: Verify DATABASE_URL in Railway environment variables

---

## 📈 FUTURE ENHANCEMENTS

### Recommended Improvements
1. **Advanced Analytics**: Track content performance across all platforms
2. **Scheduled Publishing**: Auto-publish on schedule with webhooks
3. **Team Collaboration**: Share brand strategies and content between team members
4. **CRM Integration**: Connect with customer management systems
5. **Video Scripts**: AI-generated scripts for videographers
6. **A/B Testing**: Test multiple content variations
7. **Advanced Reporting**: ROI tracking and performance dashboards

### Technical Debt: 45 Issues Identified (Nov 21, 2025 Assessment)
See **"FIRST COURSE OF ACTION"** section at top of document for full prioritized list.

**Highlights:**
- 🔴 6 Critical security issues (SQL injection risk, JWT fallback, connection leaks)
- 🟠 11 High priority architectural issues (monolithic components, no memoization)
- 🟡 15 Medium priority code quality issues
- 🟢 10 Low priority style/documentation issues

**What's Working Well:**
- ✅ Connection pooling architecture (db_pool.py) is solid
- ✅ RealDictCursor migration complete
- ✅ JWT authentication flow is secure
- ✅ Multi-tenant OAuth 2.0 implementation is comprehensive
- ✅ Credit system with PostgreSQL functions is well-designed
- ✅ TypeScript strict mode enabled
- ✅ Centralized API client design is good
- ✅ No XSS vulnerabilities

---

## 🤝 HANDOFF CHECKLIST

### Access & Credentials
- [ ] GitHub repository access
- [ ] Vercel project access
- [ ] Railway project access
- [ ] Anthropic API key
- [ ] Google Cloud Console (Drive API)
- [ ] Unsplash API key
- [ ] Social media API credentials

### Documentation
- [x] Architecture explained
- [x] Database schema documented
- [x] API endpoints listed
- [x] Environment variables documented
- [x] Deployment process explained
- [x] Local development setup

### Code Quality
- [x] Zero hardcoded URLs or credentials
- [x] Centralized configuration (lib/config.ts, backend/config.py)
- [x] Type-safe API client with TypeScript guards
- [x] Proper error handling with console.error logging
- [x] CORS configured correctly for Vercel + localhost
- [x] PostgreSQL migration complete
- [x] No TypeScript errors (8 fixed in Nov 2025)
- [x] No 'any' types (9 replaced with proper types)
- [x] No duplicate backend files (6 removed)
- [x] Secure environment variable pattern (DATABASE_URL fixed)
- [x] Optimal AI model allocation (7 providers, Nov 2025)
- [x] Social publishing infrastructure (9 platforms, Nov 7 2025)
- [x] JWT authentication with bcrypt (Nov 2025)
- [x] Multi-user support with per-user data isolation (Nov 2025)
- [x] Complete Stripe payment integration with credit management (Nov 12 2025)
- [x] Credit-based usage enforcement on all AI operations (Nov 12 2025)

---

## 📞 SUPPORT

For questions about this codebase:
1. Check this handoff document
2. Review `README.md`
3. Check API docs at `/docs` endpoint
4. Review commit history for context

**Built with ❤️ by the ORLA³ team**

---

**Last Updated**: November 22, 2025
**Architecture Version**: 7.1 (Code Assessment + Security Fixes + Connection Pool Migration + Google Verification)
**Status**: Production-ready with 7/9 social platforms live (TikTok in review, YouTube verification pending), 3-provider cloud storage, Stripe payments, credit management, OAuth 2.0 multi-tenant architecture. **45 technical debt items identified** - see "FIRST COURSE OF ACTION" section for prioritized fix list.

**Google OAuth Verification Status (Nov 22, 2025):**
- Google Search Console: `marketing.orla3.com` ownership verified via HTML file
- Verification file: `public/google892ded82cbd71f45.html`
- Privacy policy link: Added to homepage footer
- OAuth consent screen homepage: `https://marketing.orla3.com`
- Status: Waiting for Google Verification Center to sync (can take hours to days)

**Recent Session Work (Nov 20-22, 2025):**
- Fixed RealDictCursor compatibility issues (KeyError: 0 bugs)
- Fixed Facebook OAuth connection (context manager issue)
- Fixed admin.py connection pool migration (10 functions)
- YouTube OAuth verification submitted (pending Google approval)
- Comprehensive code assessment completed (45 issues documented)
- Added privacy policy link to homepage footer (required for Google verification)
- Added Google Search Console HTML verification file (`public/google892ded82cbd71f45.html`)
- Domain ownership verified in Google Search Console for `marketing.orla3.com`
- Awaiting Google OAuth Verification Center to sync with Search Console verification
