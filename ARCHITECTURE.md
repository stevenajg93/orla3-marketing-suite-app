# 🏗️ ORLA³ Marketing Suite - System Architecture

**Last Updated:** November 14, 2025
**Author:** Claude (with Steven Gillespie)
**Version:** 1.0.0

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Database Schema](#database-schema)
4. [Authentication & Authorization](#authentication--authorization)
5. [API Architecture](#api-architecture)
6. [Cloud Storage Integration](#cloud-storage-integration)
7. [Payment & Credits System](#payment--credits-system)
8. [AI Integration Strategy](#ai-integration-strategy)
9. [Social Media Publishing](#social-media-publishing)
10. [Deployment Architecture](#deployment-architecture)
11. [Security](#security)
12. [Performance](#performance)

---

## System Overview

ORLA³ is a **multi-tenant SaaS platform** for AI-powered marketing automation. The architecture is designed for scalability, security, and maintainability.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Browser                            │
│              (Next.js 15 / React / TypeScript)              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Vercel Edge Network                         │
│           (Frontend Hosting & CDN)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ API Calls (JWT Auth)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Railway Backend (FastAPI)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Auth Routes │  │ Content Gen  │  │  Publishing  │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Cloud OAuth │  │   Payments   │  │  AI Services │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┬──────────────┐
         ▼             ▼             ▼              ▼
┌──────────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐
│  PostgreSQL  │ │  Stripe   │ │ AI APIs  │ │ OAuth APIs  │
│   (Railway)  │ │    API    │ │(Multiple)│ │ (9 Platforms)
└──────────────┘ └───────────┘ └──────────┘ └─────────────┘
```

### Core Principles

1. **Multi-Tenancy**: Every resource is scoped to a `user_id`
2. **Stateless API**: JWT tokens for authentication, no server sessions
3. **Service Separation**: Frontend (Vercel) and Backend (Railway) are fully decoupled
4. **Security First**: OAuth 2.0, JWT, encrypted tokens, CORS protection
5. **Credit-Based Billing**: All AI operations deduct from user credit balance

---

## Technology Stack

### Frontend (Vercel)
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **UI Library**: React 18
- **Styling**: Tailwind CSS
- **State Management**: React Hooks (useState, useEffect)
- **API Client**: Custom fetch wrapper (`lib/api-client.ts`)
- **Authentication**: JWT stored in localStorage
- **Deployment**: Vercel (auto-deploy from GitHub)

### Backend (Railway)
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.14+
- **Server**: Uvicorn (ASGI)
- **Database ORM**: Raw SQL with psycopg2-binary
- **Authentication**: JWT (PyJWT), bcrypt password hashing
- **Scheduling**: APScheduler (background tasks)
- **Logging**: Python logging module
- **Deployment**: Railway (auto-deploy from GitHub)

### Database (Railway)
- **Type**: PostgreSQL 15+
- **Connection**: psycopg2-binary with RealDictCursor
- **Migrations**: Manual SQL scripts in `backend/migrations/`
- **Backups**: Railway automatic backups

### Third-Party Services
- **Payments**: Stripe (subscriptions, one-time purchases)
- **Email**: Resend API
- **AI Providers**:
  - Anthropic Claude Sonnet 4
  - OpenAI GPT-4o, GPT-4o-mini
  - Google Gemini 2.0 Flash
  - Google Vertex AI (Imagen 4 Ultra, Veo 3.1)
  - Perplexity AI (web research)
- **Image Search**: Unsplash, Pexels
- **Cloud Storage**: Google Drive, Dropbox, OneDrive
- **Social Platforms**: 9 platforms via OAuth 2.0

---

## Database Schema

### Core Tables

#### `users`
Multi-tenant user accounts with subscription management.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user', -- 'user', 'org_admin', 'system_admin'
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    verification_expires_at TIMESTAMPTZ,
    reset_token VARCHAR(255),
    reset_expires_at TIMESTAMPTZ,
    stripe_customer_id VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free', -- 'free', 'starter', 'pro', 'business', 'enterprise'
    subscription_status VARCHAR(50) DEFAULT 'inactive', -- 'active', 'inactive', 'cancelled', 'past_due'
    subscription_period VARCHAR(20) DEFAULT 'monthly', -- 'monthly', 'annual'
    credits INTEGER DEFAULT 0, -- Current credit balance
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `credit_transactions`
Complete audit trail of all credit changes.

```sql
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL, -- Positive for credits added, negative for usage
    transaction_type VARCHAR(50) NOT NULL, -- 'subscription_renewal', 'credit_purchase', 'ai_generation', 'image_generation', etc.
    description TEXT,
    metadata JSONB, -- Additional context (e.g., {"prompt": "...", "model": "gpt-4o"})
    stripe_payment_id VARCHAR(255), -- For purchases
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `user_cloud_storage_tokens`
OAuth tokens for Google Drive, Dropbox, OneDrive.

```sql
CREATE TABLE user_cloud_storage_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'google_drive', 'dropbox', 'onedrive'
    provider_user_id TEXT, -- Provider's user ID
    provider_email TEXT, -- User's email on the provider
    access_token TEXT NOT NULL, -- OAuth access token (encrypted in production)
    refresh_token TEXT, -- OAuth refresh token (encrypted in production)
    token_expires_at TIMESTAMPTZ, -- Token expiration timestamp
    metadata JSONB, -- Additional provider-specific data
    is_active BOOLEAN DEFAULT TRUE,
    last_refreshed_at TIMESTAMPTZ DEFAULT NOW(),
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider) -- One connection per provider per user
);
```

#### `connected_services`
Social media OAuth tokens (9 platforms).

```sql
CREATE TABLE connected_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_name VARCHAR(50) NOT NULL, -- 'twitter', 'facebook', 'instagram', 'linkedin', etc.
    service_user_id VARCHAR(255), -- Platform's user ID
    service_username VARCHAR(255), -- Platform username/handle
    access_token TEXT NOT NULL, -- OAuth access token (encrypted)
    refresh_token TEXT, -- OAuth refresh token if applicable
    token_expires_at TIMESTAMPTZ,
    scope TEXT, -- OAuth scopes granted
    service_metadata JSONB, -- Platform-specific data (e.g., Facebook page_id)
    is_active BOOLEAN DEFAULT TRUE,
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, service_name) -- One connection per service per user
);
```

#### `content_library`
User-generated content storage.

```sql
CREATE TABLE content_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL, -- 'blog', 'social_post', 'ad_copy', 'carousel', etc.
    content TEXT NOT NULL, -- The actual content
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'published', 'archived'
    platform VARCHAR(50), -- Target platform if applicable
    tags TEXT[], -- User-defined tags
    media_url TEXT, -- URL to associated media (images/videos)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_library_user_id ON content_library(user_id);
CREATE INDEX idx_content_library_created_at ON content_library(created_at DESC);
```

#### `scheduled_posts`
Social media posts scheduled for future publication.

```sql
CREATE TABLE scheduled_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL, -- 'twitter', 'facebook', 'instagram', etc.
    content TEXT NOT NULL,
    media_urls TEXT[], -- Array of media URLs
    scheduled_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'published', 'failed'
    error_message TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scheduled_posts_user_platform ON scheduled_posts(user_id, platform);
CREATE INDEX idx_scheduled_posts_scheduled_time ON scheduled_posts(scheduled_time);
CREATE INDEX idx_scheduled_posts_status ON scheduled_posts(status);
```

#### `oauth_states`
PKCE state management for OAuth flows.

```sql
CREATE TABLE oauth_states (
    state VARCHAR(255) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL, -- 'twitter', 'google_drive', etc.
    code_verifier VARCHAR(255), -- PKCE code verifier (for Twitter)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_oauth_states_created_at ON oauth_states(created_at);
```

### Migration Strategy

Migrations are stored in `backend/migrations/` as numbered SQL files:
- `001_initial_schema.sql`
- `002_multi_tenant.sql`
- `003_stripe_integration.sql`
- `004_cloud_storage.sql`
- `005_social_publishing.sql`
- `006_oauth_states.sql`

Apply migrations manually using Python scripts like `backend/apply_migration.py`.

---

## Authentication & Authorization

### JWT-Based Authentication

#### Flow
1. **Registration**: User creates account → email verification required
2. **Login**: User submits credentials → server validates → returns JWT tokens
3. **Authorization**: Frontend sends `Authorization: Bearer <token>` with every API request
4. **Token Validation**: Backend middleware decodes JWT, extracts `user_id`, attaches to `request.state`

#### Token Structure

**Access Token** (60 minutes):
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "user",
  "type": "access",
  "exp": 1763156890,
  "iat": 1763153290
}
```

**Refresh Token** (30 days):
```json
{
  "sub": "user-uuid",
  "type": "refresh",
  "exp": 1765745290,
  "iat": 1763153290
}
```

#### Middleware: `UserContextMiddleware`

Location: `backend/middleware/user_context.py`

```python
class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Default to System User (for backward compatibility)
        user_id = SYSTEM_USER_ID  # 00000000-0000-0000-0000-000000000000
        user_role = 'system_admin'

        # Extract JWT from Authorization header
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            payload = decode_token(token)

            if payload and payload.get('type') == 'access':
                user_id = uuid.UUID(payload.get('sub'))
                user_role = payload.get('role', 'user')

        # Attach to request state
        request.state.user_id = user_id
        request.state.user_role = user_role

        return await call_next(request)
```

**Helper Function**:
```python
def get_user_id(request: Request) -> uuid.UUID:
    return request.state.user_id
```

### Password Security
- **Hashing**: bcrypt with auto-generated salt
- **Strength Requirements**: 8+ chars, uppercase, lowercase, number
- **Reset Tokens**: URL-safe random tokens with expiration

---

## API Architecture

### Route Organization

Backend routes are organized by feature in `backend/routes/`:

```
routes/
├── auth.py                    # Registration, login, password reset
├── payment.py                 # Stripe checkout, webhooks
├── credits.py                 # Credit balance, transaction history
├── cloud_storage_oauth.py     # OAuth for Google Drive, Dropbox, OneDrive
├── cloud_storage_browse.py    # File browsing from cloud providers
├── social_auth.py             # OAuth for 9 social platforms
├── social_engagement.py       # Comment replies, mentions
├── social_discovery.py        # Keyword search, trending topics
├── library.py                 # Content CRUD operations
├── ai_generation.py           # Imagen 4 Ultra, Veo 3.1
├── carousel.py                # Carousel content generation
├── social_caption.py          # Social media captions
├── publisher.py               # Social media publishing
├── draft.py                   # Draft management
├── calendar.py                # Content calendar
├── competitor.py              # Competitor tracking & analysis
├── strategy.py                # Brand strategy synthesis
├── brand_voice.py             # Brand voice management
├── brand_voice_upload.py      # Brand asset uploads
├── brand_assets.py            # Brand asset retrieval
└── debug.py                   # Diagnostic endpoints (remove in production)
```

### CORS Configuration

Location: `backend/main.py`

```python
allowed_origins = [
    "http://localhost:3000",              # Local dev
    "https://orla3-marketing-suite-app.vercel.app",  # Production
    "https://marketing.orla3.com",        # Custom domain
    os.getenv("FRONTEND_URL", "")         # Environment variable
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)
```

### Error Handling

All routes use FastAPI's `HTTPException` for consistent error responses:

```python
raise HTTPException(
    status_code=404,
    detail="Content not found or not owned by user"
)
```

Frontend receives:
```json
{
  "detail": "Content not found or not owned by user"
}
```

---

## Cloud Storage Integration

### Supported Providers
1. **Google Drive** (OAuth 2.0)
2. **Dropbox** (OAuth 2.0)
3. **OneDrive** (OAuth 2.0)

### OAuth Flow

#### 1. Initiate OAuth
`GET /cloud-storage/oauth/{provider}/auth`
- Generates OAuth authorization URL
- Creates PKCE state for security
- Redirects user to provider's login

#### 2. OAuth Callback
`GET /cloud-storage/oauth/{provider}/callback?code=...&state=...`
- Validates state parameter
- Exchanges authorization code for access token
- Stores tokens in `user_cloud_storage_tokens` table
- Redirects to frontend success page

#### 3. Browse Files
`GET /cloud-storage/browse/{provider}?folder_id=...`
- Retrieves user's access token from database
- Calls provider's API to list files/folders
- Returns standardized file list

#### 4. Disconnect
`DELETE /cloud-storage/connections/{provider}`
- Revokes OAuth token with provider
- Deletes token from database
- Marks connection as inactive

### Token Refresh Strategy

**Google Drive & OneDrive**: Use refresh tokens to get new access tokens when expired.

```python
if token_is_expired(connection['token_expires_at']):
    new_token = refresh_access_token(connection['refresh_token'])
    update_token_in_database(user_id, provider, new_token)
```

**Dropbox**: Access tokens are long-lived (no refresh needed).

### Security Considerations
- **Tokens**: Stored in database (should be encrypted in production)
- **Scopes**: Limited to file reading only (no deletion/modification)
- **Folder Restrictions**: Users can limit access to specific folders
- **Token Revocation**: Properly revoke tokens on disconnect

---

## Payment & Credits System

### Stripe Integration

#### Subscription Tiers

| Tier          | Monthly | Annual  | Credits/Month |
|---------------|---------|---------|---------------|
| **Starter**   | £25     | £250    | 1,000         |
| **Professional** | £75  | £750    | 3,500         |
| **Business**  | £150    | £1,500  | 8,000         |
| **Enterprise**| £300    | -       | 20,000        |

#### Credit Top-Ups (One-Time Purchases)

| Package | Price | Credits |
|---------|-------|---------|
| Small   | £10   | 500     |
| Medium  | £18   | 1,000   |
| Large   | £40   | 2,500   |
| Mega    | £75   | 5,000   |

### Credit Deduction Rates

| Operation               | Credits Deducted |
|-------------------------|------------------|
| Blog Generation         | 50               |
| Carousel Generation     | 30               |
| Social Caption          | 10               |
| Comment Reply           | 5                |
| Image Generation (Imagen)| 20              |
| Video Generation (Veo)  | 200              |
| Competitor Analysis     | 25               |
| Strategy Synthesis      | 40               |

### Payment Flow

#### Checkout
1. Frontend: User selects plan → `POST /payment/create-checkout-session`
2. Backend: Creates Stripe checkout session → returns `session_url`
3. Frontend: Redirects to Stripe hosted checkout
4. User completes payment on Stripe
5. Stripe redirects to `{FRONTEND_URL}/dashboard?payment=success`

#### Webhook Handling
`POST /payment/stripe/webhook` (Stripe signature verification)

**Events Handled**:
- `checkout.session.completed`: Update user subscription, add credits
- `invoice.payment_succeeded`: Renew subscription, add monthly credits
- `customer.subscription.deleted`: Downgrade user to free tier

### Credit Transaction Tracking

Every credit change is logged in `credit_transactions`:

```python
# Credit usage example
cursor.execute("""
    INSERT INTO credit_transactions
    (user_id, amount, transaction_type, description, metadata)
    VALUES (%s, %s, %s, %s, %s)
""", (
    user_id,
    -50,  # Negative for usage
    'blog_generation',
    'Generated blog post',
    {'prompt': '...', 'model': 'claude-sonnet-4', 'word_count': 1200}
))

# Update user balance
cursor.execute("""
    UPDATE users
    SET credits = credits - 50
    WHERE id = %s
""", (user_id,))
```

---

## AI Integration Strategy

### Multi-Provider Optimization

Different AI providers are used based on task requirements:

| Provider            | Use Case                           | Why                                    |
|---------------------|------------------------------------|----------------------------------------|
| **Claude Sonnet 4** | Strategic analysis, brand-critical | Best reasoning, context understanding  |
| **GPT-4o**          | Creative, conversational content   | Natural language, engaging tone        |
| **Gemini 2.0 Flash**| Structured visual content          | Fast, handles images/carousels well    |
| **Perplexity AI**   | Real-time web research             | Web search, competitor intelligence    |
| **GPT-4o-mini**     | Simple analytical tasks            | Cost-effective for basic operations    |
| **Imagen 4 Ultra**  | AI image generation                | Photorealistic quality                 |
| **Veo 3.1**         | AI video generation                | 8-second videos with audio             |

### API Key Management

All API keys stored in environment variables:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `PERPLEXITY_API_KEY`
- `GCP_PROJECT_ID`, `GCP_CLIENT_ID`, `GCP_CLIENT_SECRET`, `GCP_REFRESH_TOKEN` (Vertex AI)

### Google Vertex AI (Imagen & Veo)

Uses OAuth 2.0 with refresh tokens for authentication:

```python
from google.oauth2.credentials import Credentials
from google.cloud import aiplatform

credentials = Credentials(
    token=None,
    refresh_token=GCP_REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=GCP_CLIENT_ID,
    client_secret=GCP_CLIENT_SECRET
)

aiplatform.init(
    project=GCP_PROJECT_ID,
    credentials=credentials
)
```

---

## Social Media Publishing

### Supported Platforms

| Platform       | Status      | OAuth Method         | Publishing Method             |
|----------------|-------------|----------------------|-------------------------------|
| **Twitter/X**  | ✅ Working  | OAuth 2.0 + PKCE     | POST /2/tweets                |
| **Facebook**   | ✅ Working  | OAuth 2.0            | POST /{page-id}/feed          |
| **Instagram**  | ✅ Working  | Facebook Login       | POST /media, POST /media_publish |
| **LinkedIn**   | ✅ Working  | OpenID Connect       | POST /ugcPosts                |
| **YouTube**    | ✅ Working  | Google OAuth         | POST /upload/youtube/v3/videos |
| **Reddit**     | ✅ Working  | OAuth 2.0            | POST /api/submit              |
| **Tumblr**     | ✅ Working  | OAuth 2.0            | POST /blog/{blog}/post        |
| **WordPress**  | ✅ Working  | OAuth 2.0            | POST /wp/v2/posts             |
| **TikTok**     | ⏳ In Review| OAuth 2.0            | POST /v2/post/publish/video/init |

### Universal Publishing Endpoint

`POST /social/publish`

**Request Body**:
```json
{
  "platform": "twitter",
  "content": "Check out our new product! 🚀",
  "media_urls": ["https://example.com/image.jpg"]
}
```

**Flow**:
1. Verify user has connected the platform
2. Retrieve OAuth tokens from `connected_services` table
3. Call platform-specific API
4. Return success/error response

### Token Storage

OAuth tokens stored in `connected_services` table:
```python
{
  "user_id": "user-uuid",
  "service_name": "twitter",
  "access_token": "encrypted-token",
  "refresh_token": "encrypted-refresh-token",
  "token_expires_at": "2025-12-31T23:59:59Z",
  "service_metadata": {"page_id": "123456789"}  # Facebook only
}
```

---

## Deployment Architecture

### Frontend: Vercel

**Repository**: GitHub → Auto-deploy on push to `main`

**Environment Variables**:
```bash
NEXT_PUBLIC_API_URL=https://orla3-marketing-suite-app-production.up.railway.app
```

**Build Command**: `npm run build`
**Output Directory**: `.next`
**Framework**: Next.js

### Backend: Railway

**Repository**: GitHub → Auto-deploy on push to `main`

**Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment Variables**: See `backend/RAILWAY_ENVIRONMENT_VARIABLES.md`

**Resource Limits** (Free Tier):
- RAM: 512MB
- CPU: Shared vCPU
- Execution Time: 500 hours/month

### Database: Railway PostgreSQL

**Version**: PostgreSQL 15+
**Backups**: Automatic daily backups
**Connection**: Uses `DATABASE_URL` environment variable

---

## Security

### Best Practices Implemented

1. **Authentication**
   - JWT tokens with 1-hour expiration
   - bcrypt password hashing with salt
   - Email verification required

2. **Authorization**
   - All database queries filtered by `user_id`
   - Role-based access control (`user`, `org_admin`, `system_admin`)

3. **Data Protection**
   - CORS configured for allowed origins only
   - Environment variables for secrets
   - OAuth tokens should be encrypted at rest (TODO)

4. **API Security**
   - Rate limiting (TODO)
   - Input validation with Pydantic models
   - HTTPException for consistent error handling

5. **OAuth Security**
   - PKCE for Twitter OAuth (SHA256 code challenge)
   - State parameter validation
   - Token revocation on disconnect

### Security Improvements Needed (TODO)

1. **Encrypt OAuth Tokens**: Currently stored as plaintext in database
2. **Rate Limiting**: Add per-user API rate limits
3. **IP Whitelisting**: For admin endpoints
4. **2FA**: Two-factor authentication for high-value accounts
5. **Audit Logging**: Track all sensitive operations

---

## Performance

### Current Optimizations

1. **Database**
   - Indexes on frequently queried columns
   - Connection pooling (psycopg2)

2. **Frontend**
   - Next.js static generation where possible
   - Lazy loading for large components

3. **API**
   - Async endpoints with FastAPI
   - Background tasks with APScheduler

### Performance Improvements Needed (TODO)

1. **Caching**: Redis for frequently accessed data
2. **CDN**: Cloudflare for static assets
3. **Database Connection Pool**: Implement proper pooling
4. **Query Optimization**: Review slow queries with EXPLAIN
5. **Frontend Code Splitting**: Reduce bundle size

---

## File Structure Reference

```
orla3-marketing-suite-app/
├── app/                          # Next.js frontend
│   ├── dashboard/                # Dashboard pages
│   ├── auth/                     # Auth pages (login, register)
│   └── payment/                  # Payment pages
├── backend/                      # FastAPI backend
│   ├── routes/                   # API routes
│   ├── middleware/               # Auth middleware
│   ├── utils/                    # Helper functions
│   ├── migrations/               # Database migrations
│   ├── main.py                   # FastAPI app entry point
│   └── requirements.txt          # Python dependencies
├── lib/                          # Frontend utilities
│   ├── api-client.ts             # API wrapper with JWT
│   └── config.ts                 # Frontend config
├── components/                   # React components
├── public/                       # Static assets
├── .env.local                    # Frontend env vars
├── backend/.env                  # Backend env vars
├── README.md                     # Project overview
├── ARCHITECTURE.md               # This file
├── SETUP.md                      # Setup instructions
└── JUNIOR_DEV_GUIDE.md           # Onboarding guide
```

---

## Common Debugging Tips

### Backend Not Receiving Auth Header

**Symptom**: Endpoints return "No active connection found" even though user is logged in

**Cause**: Frontend not sending `Authorization: Bearer <token>` header

**Fix**:
1. Check `localStorage.getItem('access_token')` in browser console
2. Hard refresh frontend (Cmd+Shift+R) to clear cache
3. Verify API client in `lib/api-client.ts` adds auth header

### CORS Errors

**Symptom**: `Access-Control-Allow-Origin` errors in browser console

**Cause**: Backend endpoint crashing before CORS middleware runs

**Fix**:
1. Check backend logs for actual error
2. Ensure `HTTPException` is raised (not generic Python exceptions)
3. Verify CORS allowed origins in `backend/main.py`

### UUID Errors in PostgreSQL

**Symptom**: `can't adapt type 'UUID'`

**Cause**: psycopg2 can't handle Python UUID objects

**Fix**: Convert to string before query: `str(user_id)`

---

**End of Architecture Documentation**
