# Multi-Tenant Cloud Storage Architecture Implementation Plan

## Problem Statement

Your current architecture has **critical multi-tenancy issues**:

1. **Google Drive**: Single shared drive (`SHARED_DRIVE_ID`) - all users access the same Drive
2. **OneDrive**: Global environment variables - not per-user
3. **Database**: No `user_id` foreign keys - all data shared across users

**Result**: Every user sees the same brand strategy, competitors, content, and cloud files. Not suitable for SaaS.

## Solution Overview

Implement proper multi-tenant architecture where:
- Each user connects their own Google Drive/OneDrive/Dropbox
- Each user has their own brand strategy, content, competitors
- OAuth tokens stored per-user in database (encrypted)
- All API routes filtered by authenticated user

---

## Phase 1: Database Migration ✅ COMPLETE

**File**: `backend/migrations/001_add_multi_tenant_architecture.sql`

**Changes**:
1. ✅ Created `users` table (authentication)
2. ✅ Created `refresh_tokens` table (JWT authentication)
3. ✅ Created `audit_log` table (security tracking)
4. ✅ Created `user_cloud_storage_tokens` table (per-user OAuth tokens)
5. ✅ Added `user_id` foreign keys to ALL existing tables:
   - `brand_strategy`
   - `brand_voice_assets`
   - `competitors`
   - `content_library`
   - `content_calendar`
   - `published_posts`
6. ✅ Added brand asset columns (`brand_colors`, `brand_fonts`, `logo_url`)
7. ✅ Updated category constraints to new categories

**Apply Migration**:
```bash
# Railway CLI
psql $DATABASE_URL < migrations/001_add_multi_tenant_architecture.sql

# Or Railway Dashboard
# Copy/paste SQL into Railway PostgreSQL query runner
```

---

## Phase 2: OAuth Flow Implementation (PENDING)

### 2.1 Create OAuth Routes

**File**: `backend/routes/cloud_storage_oauth.py` (NEW)

```python
"""
OAuth routes for connecting user cloud storage accounts
Supports: Google Drive, OneDrive, Dropbox
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
import os
from typing import Literal

router = APIRouter()

# ============================================================================
# OAUTH CONFIGURATION
# ============================================================================

GOOGLE_DRIVE_CONFIG = {
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "scopes": [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file"
    ]
}

ONEDRIVE_CONFIG = {
    "client_id": os.getenv("ONEDRIVE_CLIENT_ID"),
    "client_secret": os.getenv("ONEDRIVE_CLIENT_SECRET"),
    "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
    "scopes": ["Files.Read", "Files.Read.All", "offline_access"]
}

DROPBOX_CONFIG = {
    "client_id": os.getenv("DROPBOX_CLIENT_ID"),
    "client_secret": os.getenv("DROPBOX_CLIENT_SECRET"),
    "auth_url": "https://www.dropbox.com/oauth2/authorize",
    "token_url": "https://api.dropboxapi.com/oauth2/token",
    "scopes": ["files.content.read"]
}

# ============================================================================
# STEP 1: INITIATE OAUTH FLOW
# ============================================================================

@router.get("/cloud-storage/connect/{provider}")
async def initiate_oauth(
    provider: Literal["google_drive", "onedrive", "dropbox"],
    request: Request,
    user_id: str = Depends(get_current_user_id)  # TODO: Add auth dependency
):
    """
    Step 1: Redirect user to cloud provider's OAuth consent screen

    Flow:
    1. User clicks "Connect Google Drive" in frontend
    2. Frontend calls this endpoint
    3. Backend generates OAuth URL
    4. Redirect user to provider's consent screen
    5. User authorizes
    6. Provider redirects back to /callback endpoint
    """
    # Get provider config
    if provider == "google_drive":
        config = GOOGLE_DRIVE_CONFIG
    elif provider == "onedrive":
        config = ONEDRIVE_CONFIG
    elif provider == "dropbox":
        config = DROPBOX_CONFIG
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")

    # Build OAuth URL
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_uri = f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/{provider}"

    # Generate state parameter (CSRF protection) - store user_id
    state = generate_state_token(user_id, provider)

    from urllib.parse import urlencode
    params = {
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(config["scopes"]),
        "state": state,
        "access_type": "offline",  # Google Drive: get refresh token
        "prompt": "consent"  # Force consent to get refresh token
    }

    oauth_url = f"{config['auth_url']}?{urlencode(params)}"

    return RedirectResponse(url=oauth_url)


# ============================================================================
# STEP 2: OAUTH CALLBACK
# ============================================================================

@router.get("/cloud-storage/callback/{provider}")
async def oauth_callback(
    provider: Literal["google_drive", "onedrive", "dropbox"],
    code: str,
    state: str,
    error: str = None
):
    """
    Step 2: Handle OAuth callback from cloud provider

    Flow:
    1. Provider redirects here with authorization code
    2. Verify state parameter (CSRF protection)
    3. Exchange code for access + refresh tokens
    4. Store tokens in database (encrypted)
    5. Redirect user back to frontend dashboard
    """
    if error:
        # User denied access
        frontend_url = os.getenv("FRONTEND_URL")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?cloud_connect=error&message={error}"
        )

    # Verify state and extract user_id
    user_id = verify_state_token(state, provider)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Get provider config
    if provider == "google_drive":
        config = GOOGLE_DRIVE_CONFIG
    elif provider == "onedrive":
        config = ONEDRIVE_CONFIG
    elif provider == "dropbox":
        config = DROPBOX_CONFIG

    # Exchange code for tokens
    import httpx
    redirect_uri = f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/{provider}"

    token_data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(config["token_url"], data=token_data)

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Token exchange failed: {response.text}"
            )

        tokens = response.json()

    # Get provider user info (optional but recommended)
    provider_user_id, provider_email = await get_provider_user_info(
        provider, tokens["access_token"]
    )

    # Store tokens in database (encrypted)
    from datetime import datetime, timedelta
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
    cur = conn.cursor()

    try:
        # Encrypt tokens before storing
        encrypted_access = encrypt_token(tokens["access_token"])
        encrypted_refresh = encrypt_token(tokens["refresh_token"])

        expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))

        # Upsert: Update if exists, insert if not
        cur.execute("""
            INSERT INTO user_cloud_storage_tokens (
                user_id, provider, access_token, refresh_token, token_expires_at,
                provider_user_id, provider_email, is_active, connected_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, true, NOW())
            ON CONFLICT (user_id, provider)
            DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_expires_at = EXCLUDED.token_expires_at,
                provider_user_id = EXCLUDED.provider_user_id,
                provider_email = EXCLUDED.provider_email,
                is_active = true,
                updated_at = NOW()
        """, (
            user_id, provider, encrypted_access, encrypted_refresh, expires_at,
            provider_user_id, provider_email
        ))

        conn.commit()

        logger.info(f"✅ {provider} connected for user {user_id}")

        # Redirect back to frontend
        frontend_url = os.getenv("FRONTEND_URL")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?cloud_connect=success&provider={provider}"
        )

    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing cloud tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user_id(request: Request) -> str:
    """Extract user_id from JWT token"""
    # TODO: Implement JWT validation
    # For now, placeholder
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.replace("Bearer ", "")
    # Decode JWT, extract user_id
    from utils.auth import decode_token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload["sub"]


def generate_state_token(user_id: str, provider: str) -> str:
    """Generate CSRF state token"""
    import jwt
    import os
    from datetime import datetime, timedelta

    payload = {
        "user_id": user_id,
        "provider": provider,
        "exp": datetime.utcnow() + timedelta(minutes=10)
    }

    return jwt.encode(payload, os.getenv("JWT_SECRET", "secret"), algorithm="HS256")


def verify_state_token(state: str, provider: str) -> str | None:
    """Verify state token and return user_id"""
    import jwt
    import os

    try:
        payload = jwt.decode(state, os.getenv("JWT_SECRET", "secret"), algorithms=["HS256"])
        if payload.get("provider") != provider:
            return None
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def encrypt_token(token: str) -> str:
    """Encrypt OAuth token before storing in database"""
    # TODO: Implement proper encryption (use Fernet or pgcrypto)
    # For now, store as-is (NOT PRODUCTION READY)
    return token


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt OAuth token from database"""
    # TODO: Implement decryption
    return encrypted_token


async def get_provider_user_info(provider: str, access_token: str) -> tuple[str, str]:
    """Get user info from cloud provider"""
    import httpx

    if provider == "google_drive":
        url = "https://www.googleapis.com/oauth2/v2/userinfo"
    elif provider == "onedrive":
        url = "https://graph.microsoft.com/v1.0/me"
    elif provider == "dropbox":
        url = "https://api.dropboxapi.com/2/users/get_current_account"

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(url, headers=headers) if provider != "dropbox" else await client.post(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if provider == "google_drive":
                return data.get("id"), data.get("email")
            elif provider == "onedrive":
                return data.get("id"), data.get("mail") or data.get("userPrincipalName")
            elif provider == "dropbox":
                return data.get("account_id"), data.get("email")

    return None, None
```

### 2.2 Update Existing Drive Routes

**File**: `backend/routes/drive.py` (MODIFY)

**Changes Needed**:
1. Add `user_id` parameter to all functions
2. Get user's cloud token from database instead of `token.pickle`
3. Filter Drive files by user

**Example**:
```python
# OLD (global shared drive)
def get_drive_service():
    token_path = 'credentials/token.pickle'
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)
    return build('drive', 'v3', credentials=creds)

# NEW (per-user tokens)
def get_drive_service(user_id: str):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT access_token, refresh_token, token_expires_at
        FROM user_cloud_storage_tokens
        WHERE user_id = %s AND provider = 'google_drive' AND is_active = true
    """, (user_id,))

    token_record = cur.fetchone()
    cur.close()
    conn.close()

    if not token_record:
        return None  # User hasn't connected Google Drive

    # Decrypt tokens
    access_token = decrypt_token(token_record['access_token'])
    refresh_token = decrypt_token(token_record['refresh_token'])

    # Check if token expired, refresh if needed
    if token_record['token_expires_at'] < datetime.utcnow():
        access_token = refresh_google_drive_token(user_id, refresh_token)

    # Build credentials
    from google.oauth2.credentials import Credentials
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )

    return build('drive', 'v3', credentials=creds)
```

---

## Phase 3: Update All API Routes (PENDING)

**Every API route** must:
1. Get `user_id` from JWT token (authentication)
2. Filter database queries by `user_id`
3. Ensure data isolation between users

### 3.1 Add Authentication Dependency

**File**: `backend/utils/auth_dependency.py` (NEW)

```python
"""
FastAPI dependency for user authentication
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.auth import decode_token

security = HTTPBearer()

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate user_id from JWT token

    Usage in routes:
    @router.get("/my-route")
    async def my_route(user_id: str = Depends(get_current_user_id)):
        # user_id is automatically extracted and validated
        pass
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload["sub"]  # user_id
```

### 3.2 Update Route Examples

**Before**:
```python
@router.get("/brand-assets")
async def get_brand_assets():
    cur.execute("SELECT * FROM brand_strategy ORDER BY created_at DESC LIMIT 1")
    # Returns same data for all users ❌
```

**After**:
```python
from utils.auth_dependency import get_current_user_id

@router.get("/brand-assets")
async def get_brand_assets(user_id: str = Depends(get_current_user_id)):
    cur.execute("""
        SELECT * FROM brand_strategy
        WHERE user_id = %s
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    # Returns user-specific data ✅
```

**Files to Update**:
- ✅ `routes/brand_assets.py` - Add user_id filtering
- ✅ `routes/brand_voice_upload.py` - Add user_id to inserts
- ✅ `routes/strategy.py` - Filter by user_id
- ✅ `routes/competitors.py` - Filter by user_id
- ✅ `routes/content.py` - Filter by user_id
- ✅ `routes/drive.py` - Use per-user tokens

---

## Phase 4: Frontend Updates (PENDING)

### 4.1 Add Cloud Storage Connection UI

**File**: `app/dashboard/settings/page.tsx` (NEW TAB)

```tsx
export default function CloudStorageSettings() {
  return (
    <div>
      <h2>Cloud Storage Connections</h2>

      {/* Google Drive */}
      <div>
        <h3>Google Drive</h3>
        {isConnected('google_drive') ? (
          <div>
            ✅ Connected as {providerEmail}
            <button onClick={() => disconnectProvider('google_drive')}>
              Disconnect
            </button>
          </div>
        ) : (
          <button onClick={() => connectProvider('google_drive')}>
            Connect Google Drive
          </button>
        )}
      </div>

      {/* OneDrive */}
      <div>
        <h3>Microsoft OneDrive</h3>
        {isConnected('onedrive') ? (
          <div>✅ Connected</div>
        ) : (
          <button onClick={() => connectProvider('onedrive')}>
            Connect OneDrive
          </button>
        )}
      </div>

      {/* Dropbox */}
      <div>
        <h3>Dropbox</h3>
        {isConnected('dropbox') ? (
          <div>✅ Connected</div>
        ) : (
          <button onClick={() => connectProvider('dropbox')}>
            Connect Dropbox
          </button>
        )}
      </div>
    </div>
  );
}

function connectProvider(provider: string) {
  // Redirect to backend OAuth endpoint
  window.location.href = `${config.apiUrl}/cloud-storage/connect/${provider}`;
}
```

### 4.2 Add JWT Token to All API Requests

Ensure frontend sends JWT token in all requests:

```typescript
// utils/api.ts
const token = localStorage.getItem('access_token');

const response = await fetch(`${config.apiUrl}/endpoint`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

---

## Phase 5: Deployment Checklist

### 5.1 Railway Environment Variables

**Already Configured**:
- ✅ `DATABASE_URL` (auto-injected)
- ✅ `OPENAI_API_KEY`
- ✅ `ANTHROPIC_API_KEY`
- ✅ `GCP_PROJECT_ID`
- ✅ `GCP_CLIENT_ID`
- ✅ `GCP_CLIENT_SECRET`
- ✅ `GCP_REFRESH_TOKEN`

**Need to Add**:
```bash
# OneDrive (from Azure)
ONEDRIVE_CLIENT_ID=YOUR_ONEDRIVE_CLIENT_ID
ONEDRIVE_CLIENT_SECRET=YOUR_ONEDRIVE_CLIENT_SECRET
ONEDRIVE_REFRESH_TOKEN=<long_token_from_get_onedrive_token.py>

# JWT Authentication
JWT_SECRET=<generate_random_secret>  # Use: openssl rand -hex 32

# OAuth Redirect URIs
FRONTEND_URL=https://your-app.vercel.app
BACKEND_URL=https://your-app.railway.app
```

### 5.2 Azure Redirect URI Configuration

Add production callback URLs to Azure app:
```
Web redirect URIs:
- http://localhost:8080 (development)
- https://your-app.railway.app/cloud-storage/callback/onedrive (production)
```

### 5.3 Google Cloud Console

Add production callback URLs:
```
Authorized redirect URIs:
- http://localhost:8080 (development)
- https://your-app.railway.app/cloud-storage/callback/google_drive (production)
```

---

## Migration Steps

### Step 1: Apply Database Migration
```bash
# Railway CLI
railway run psql $DATABASE_URL < migrations/001_add_multi_tenant_architecture.sql

# Or Railway Dashboard: Copy SQL to query runner
```

### Step 2: Create First Admin User
```bash
# Register via API
curl -X POST https://your-app.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin User",
    "email": "admin@example.com",
    "password": "SecurePass123!",
    "organization_name": "My Company"
  }'
```

### Step 3: Update Existing Data (if any)
```sql
-- Assign existing data to first user (if you have test data)
UPDATE brand_strategy SET user_id = (SELECT id FROM users LIMIT 1);
UPDATE brand_voice_assets SET user_id = (SELECT id FROM users LIMIT 1);
UPDATE competitors SET user_id = (SELECT id FROM users LIMIT 1);
-- etc.
```

### Step 4: Deploy Code Changes
```bash
git add .
git commit -m "Add multi-tenant architecture"
git push origin main  # Railway auto-deploys
```

---

## Testing Plan

### Test Case 1: User Registration & Login
1. Register new user via `/auth/register`
2. Login via `/auth/login`
3. Get user info via `/auth/me`
4. Verify JWT tokens work

### Test Case 2: Cloud Storage OAuth
1. User A connects Google Drive
2. Verify tokens stored in database
3. User B connects different Google Drive
4. Verify User A and B have separate tokens

### Test Case 3: Data Isolation
1. User A uploads brand guidelines
2. User B uploads different brand guidelines
3. Verify User A only sees their data
4. Verify User B only sees their data

---

## Security Considerations

1. **Token Encryption**: Implement proper encryption for OAuth tokens in database
   - Use `pgcrypto` extension or application-level encryption (Fernet)

2. **JWT Secret**: Use strong random secret, never commit to git
   ```bash
   openssl rand -hex 32
   ```

3. **HTTPS Only**: Enforce HTTPS in production for OAuth redirects

4. **Rate Limiting**: Add rate limiting to OAuth endpoints to prevent abuse

5. **Token Refresh**: Implement automatic token refresh before expiry

---

## Rollback Plan

If issues occur:

```sql
-- Rollback: Drop new tables (WARNING: Deletes all user data)
DROP TABLE IF EXISTS user_cloud_storage_tokens CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS refresh_tokens CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Remove user_id columns from existing tables
ALTER TABLE brand_strategy DROP COLUMN IF EXISTS user_id;
ALTER TABLE brand_voice_assets DROP COLUMN IF EXISTS user_id;
-- etc.
```

---

## Next Steps

1. ✅ **Database Migration**: Apply `001_add_multi_tenant_architecture.sql`
2. ⏳ **OAuth Routes**: Implement `cloud_storage_oauth.py`
3. ⏳ **Update Routes**: Add user_id filtering to all routes
4. ⏳ **Frontend UI**: Add cloud storage connection settings
5. ⏳ **Testing**: Test with multiple users
6. ⏳ **Deploy**: Push to Railway + Vercel

---

## Support

Questions or issues? Check:
- Railway database logs for migration errors
- Backend logs for OAuth flow debugging
- Azure Portal > Enterprise Applications > Sign-in logs
