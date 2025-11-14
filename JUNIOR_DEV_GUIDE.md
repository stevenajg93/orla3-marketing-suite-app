# 👋 Welcome to ORLA³ - Junior Developer Onboarding Guide

**Welcome aboard!** This guide will get you from zero to productive in 1-2 days. No prior experience with this codebase required!

---

## 🎯 Day 1: Getting Started (2-4 hours)

### Step 1: Clone and Setup (30 mins)

```bash
# 1. Clone the repository
git clone https://github.com/stevenajg93/orla3-marketing-suite-app.git
cd orla3-marketing-suite-app

# 2. Install Node.js dependencies (frontend)
npm install

# 3. Install Python dependencies (backend)
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### Step 2: Environment Variables (15 mins)

**Frontend** (`.env.local` in project root):
```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend** (`backend/.env`):
```bash
cd backend
cp .env.example .env
```

For now, use the Railway production database URL (ask your team lead for credentials).

### Step 3: Run the Application (15 mins)

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Terminal 2 - Frontend**:
```bash
npm run dev
```

You should see:
```
  ▲ Next.js 15.0.3
  - Local:        http://localhost:3000
```

**Open your browser**: http://localhost:3000

You should see the ORLA³ landing page!

### Step 4: Create an Account (10 mins)

1. Click "Get Started" or "Sign Up"
2. Register with your email
3. Check your email for verification link (if email is configured)
4. Log in

**Note**: If email verification isn't working locally, ask your team lead to manually verify your account in the database.

### Step 5: Explore the Dashboard (30 mins)

Take a tour of the key features:

1. **Dashboard Home** - Overview
2. **Media Library** - Cloud storage integration
3. **Social Manager** - Publishing to social platforms
4. **Brand Strategy** - Brand voice and competitive analysis
5. **Content Calendar** - Scheduled posts

Try clicking around and see what happens!

---

## 📚 Day 2: Understanding the Codebase (3-5 hours)

### Frontend Architecture (Next.js)

#### Key Directories

```
app/
├── dashboard/          # Main app pages
│   ├── media/         # Media library page
│   ├── social/        # Social manager page
│   └── ...
├── auth/              # Login/Register pages
└── payment/           # Stripe payment pages

components/            # Reusable React components
lib/
├── api-client.ts      # ⭐ API wrapper (READ THIS FIRST!)
└── config.ts          # Frontend configuration
```

#### How API Calls Work

**Read this file first**: `lib/api-client.ts`

Every API call goes through the `api` object:

```typescript
import { api } from '@/lib/api-client';

// GET request
const data = await api.get('/library/content');

// POST request
const result = await api.post('/social/publish', {
  platform: 'twitter',
  content: 'Hello world!'
});
```

**What happens behind the scenes**:
1. Gets JWT token from `localStorage.getItem('access_token')`
2. Adds `Authorization: Bearer <token>` header
3. Calls backend API
4. Returns JSON response

**Authentication**:
When user logs in, tokens are saved to localStorage:
```typescript
localStorage.setItem('access_token', jwt_token);
localStorage.setItem('refresh_token', refresh_token);
```

#### Page Structure Example

Look at `app/dashboard/media/page.tsx`:

```typescript
'use client';  // Client-side rendering

export default function MediaPage() {
  // 1. State management
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  // 2. Load data on mount
  useEffect(() => {
    loadFiles();
  }, []);

  // 3. API call
  const loadFiles = async () => {
    setLoading(true);
    const data = await api.get('/cloud-storage/browse/google_drive');
    setFiles(data.files);
    setLoading(false);
  };

  // 4. Render UI
  return (
    <div>
      {loading ? 'Loading...' : files.map(file => ...)}
    </div>
  );
}
```

### Backend Architecture (FastAPI)

#### Key Files

```
backend/
├── main.py                 # ⭐ App entry point (READ THIS FIRST!)
├── middleware/
│   └── user_context.py     # ⭐ Authentication middleware (READ THIS!)
├── routes/
│   ├── auth.py            # Login, register
│   ├── library.py         # Content CRUD
│   ├── social_auth.py     # Social OAuth
│   └── ...
└── utils/
    └── auth.py            # JWT helpers
```

#### How Authentication Works

**Read these files**:
1. `backend/middleware/user_context.py` - Extracts JWT from request
2. `backend/utils/auth.py` - JWT creation/validation

**Flow**:
1. Frontend sends: `Authorization: Bearer <jwt>`
2. Middleware extracts token, validates it
3. Middleware adds `user_id` to `request.state.user_id`
4. Routes use `get_user_id(request)` to get current user

**Example Route**:

```python
from fastapi import APIRouter, Request
from middleware.user_context import get_user_id

router = APIRouter()

@router.get("/library/content")
def get_content(request: Request):
    # Get current user ID from JWT
    user_id = get_user_id(request)

    # Query database for THIS user's content only
    cursor.execute("""
        SELECT * FROM content_library
        WHERE user_id = %s
    """, (str(user_id),))

    items = cursor.fetchall()
    return {"items": items}
```

**Important**: Always filter by `user_id`! This is a multi-tenant app - users should never see each other's data.

#### Database Queries

We use **raw SQL** with `psycopg2`:

```python
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Example query
conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
user = cursor.fetchone()  # Returns a dict

cursor.close()
conn.close()
```

**⚠️ UUID Warning**: Always convert UUIDs to strings!

```python
# ❌ WRONG - Will crash
cursor.execute("... WHERE user_id = %s", (user_id,))

# ✅ CORRECT
cursor.execute("... WHERE user_id = %s", (str(user_id),))
```

---

## 🛠️ Your First Task: Add a "Favorite" Feature

Let's add a simple feature to practice the full stack!

### Task: Add a "favorite" button to content library items

**Requirements**:
1. Add `is_favorite` boolean column to `content_library` table
2. Create API endpoint to toggle favorite status
3. Add star icon button in Media Library UI
4. Show favorited items at the top

### Step 1: Database Migration (5 mins)

Create `backend/migrations/007_add_favorites.sql`:

```sql
ALTER TABLE content_library
ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE;
```

Apply it:

```bash
cd backend
source venv/bin/activate
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

with open('migrations/007_add_favorites.sql') as f:
    cursor.execute(f.read())

conn.commit()
cursor.close()
conn.close()
print('✅ Migration applied!')
"
```

### Step 2: Backend API Endpoint (10 mins)

Add to `backend/routes/library.py`:

```python
@router.patch("/content/{item_id}/favorite")
def toggle_favorite(item_id: str, request: Request):
    """Toggle favorite status of a content item"""
    try:
        user_id = get_user_id(request)
        user_id_str = str(user_id)
        conn = get_db_connection()
        cur = conn.cursor()

        # Toggle the favorite status
        cur.execute("""
            UPDATE content_library
            SET is_favorite = NOT is_favorite
            WHERE id = %s AND user_id = %s
            RETURNING id, is_favorite
        """, (item_id, user_id_str))

        updated_item = cur.fetchone()
        if not updated_item:
            conn.close()
            raise HTTPException(status_code=404, detail="Content not found")

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "is_favorite": updated_item['is_favorite']}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        return {"success": False, "error": str(e)}
```

**Test it**:
```bash
# Terminal with backend running
curl -X PATCH http://localhost:8000/library/content/<item-id>/favorite \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Step 3: Frontend UI (15 mins)

Edit `app/dashboard/media/page.tsx`:

```typescript
// Add toggle function
const toggleFavorite = async (itemId: string) => {
  try {
    const result = await api.patch(`/library/content/${itemId}/favorite`);

    // Update local state
    setGeneratedContent(prev =>
      prev.map(item =>
        item.id === itemId
          ? { ...item, is_favorite: result.is_favorite }
          : item
      )
    );
  } catch (err) {
    console.error('Failed to toggle favorite:', err);
  }
};

// In your content list rendering, add a button:
<button
  onClick={() => toggleFavorite(item.id)}
  className="text-yellow-500 hover:text-yellow-600"
>
  {item.is_favorite ? '⭐' : '☆'}
</button>
```

### Step 4: Sort Favorites First (5 mins)

Update the query in `backend/routes/library.py`:

```python
cur.execute("""
    SELECT * FROM content_library
    WHERE user_id = %s
    ORDER BY is_favorite DESC, created_at DESC
""", (user_id_str,))
```

Now favorites appear at the top!

### Step 5: Test It! (5 mins)

1. Refresh http://localhost:3000/dashboard/media
2. Click the star icon on any content item
3. It should turn gold and move to the top!

**Congratulations!** 🎉 You just made your first full-stack contribution!

---

## 🐛 Common Issues and Solutions

### Issue: "Module not found" errors

**Solution**: Install missing dependencies

```bash
# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### Issue: CORS errors in browser

**Symptom**: `Access-Control-Allow-Origin` error

**Solution**: Make sure backend is running and check `backend/main.py` CORS config:

```python
allowed_origins = [
    "http://localhost:3000",  # Must match your frontend URL
    ...
]
```

### Issue: "No active connection found"

**Symptom**: API returns 404 for user-specific resources

**Cause**: JWT token not being sent or invalid

**Solution**:
1. Check localStorage: `localStorage.getItem('access_token')`
2. Re-login to get a fresh token
3. Hard refresh browser (Cmd+Shift+R)

### Issue: Database errors with UUIDs

**Symptom**: `can't adapt type 'UUID'`

**Solution**: Always convert UUIDs to strings:

```python
user_id_str = str(user_id)
cursor.execute("... WHERE user_id = %s", (user_id_str,))
```

### Issue: Railway deployment out of memory

**Cause**: Too many rapid deployments

**Solution**: Wait 10-15 minutes for Railway to recover, or restart the service in Railway dashboard.

---

## 📖 Key Concepts to Understand

### Multi-Tenancy

**What it means**: Multiple users share the same app and database, but never see each other's data.

**How we enforce it**: Every table has a `user_id` column, and every query filters by it.

```python
# ✅ GOOD - Only returns current user's data
cursor.execute("SELECT * FROM content_library WHERE user_id = %s", (user_id,))

# ❌ BAD - Returns ALL users' data!
cursor.execute("SELECT * FROM content_library")
```

### JWT Tokens

**What they are**: Encrypted strings that prove who you are.

**Structure**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWlkIiwiZXhwIjoxNjM...
```

**Decoded**:
```json
{
  "sub": "user-id-here",
  "email": "user@example.com",
  "exp": 1763156890
}
```

**Where they're stored**: `localStorage` in the browser

**How they're used**: `Authorization: Bearer <token>` header on every API request

### OAuth 2.0

**What it is**: A way for users to give our app permission to access their Google Drive, Twitter, etc. without giving us their password.

**Flow**:
1. User clicks "Connect Google Drive"
2. We redirect to Google's login page
3. User approves permissions
4. Google sends us an access token
5. We store the token in our database
6. We use the token to read their files

**Key files**:
- `backend/routes/cloud_storage_oauth.py` - OAuth for cloud storage
- `backend/routes/social_auth.py` - OAuth for social platforms

---

## 🚀 Deployment

### Frontend (Vercel)

**Auto-deploys** when you push to `main` branch on GitHub.

**URL**: https://marketing.orla3.com

**Environment Variables**: Set in Vercel dashboard (ask team lead)

### Backend (Railway)

**Auto-deploys** when you push to `main` branch on GitHub.

**URL**: https://orla3-marketing-suite-app-production.up.railway.app

**Environment Variables**: Set in Railway dashboard (ask team lead)

**Important**: Backend takes ~2 minutes to deploy. If you push code, wait before testing on production.

### Testing on Production

**Frontend**: https://marketing.orla3.com
**Backend**: Check Railway logs for errors

**Debugging Production Issues**:
1. Check Railway logs: `railway logs`
2. Check Vercel deployment logs
3. Check browser console for frontend errors

---

## 📚 Recommended Reading Order

Day 1:
1. This file (JUNIOR_DEV_GUIDE.md) ✅ You're here!
2. `README.md` - Project overview
3. `SETUP.md` - Detailed setup instructions

Day 2:
4. `ARCHITECTURE.md` - Deep technical details
5. `lib/api-client.ts` - Frontend API wrapper
6. `backend/main.py` - Backend entry point
7. `backend/middleware/user_context.py` - Authentication

Day 3:
8. `MIGRATIONS.md` - Database schema evolution
9. `STRIPE_SETUP_GUIDE.md` - Payment system
10. `SOCIAL_MEDIA_SETUP.md` - Social publishing

---

## 💬 Getting Help

### Ask Questions!

**No question is too small.** We all started somewhere.

**Where to ask**:
- Slack: #dev-questions channel
- Code comments: Use `// TODO: Ask about this` and tag a senior dev
- Team meetings: Bring questions to standup

### Debugging Checklist

Before asking for help, try these steps:

1. ✅ Read the error message carefully
2. ✅ Check the browser console (F12)
3. ✅ Check backend logs (terminal where uvicorn is running)
4. ✅ Google the error message
5. ✅ Check if others had the same issue (GitHub Issues, Stack Overflow)
6. ✅ Try the "Common Issues" section above

If still stuck after 30 minutes, ask for help!

### Code Review Tips

When submitting a pull request:

1. **Test locally first** - Run both frontend and backend, test all changed features
2. **Write clear commit messages** - "Add favorite toggle to content library"
3. **Explain why, not just what** - "Added favorites so users can quickly find important content"
4. **Keep PRs small** - Easier to review 100 lines than 1000 lines
5. **Ask for feedback** - "Is this the right approach?" is a great question

---

## 🎓 Next Steps: Week 2+

### Small Tasks to Build Confidence

1. **Add a new filter** - Filter content by date range
2. **Add a new column** - Add "last_edited" timestamp to content
3. **Improve error messages** - Make error messages more user-friendly
4. **Add loading states** - Show spinners while data loads
5. **Fix a bug** - Pick one from GitHub Issues

### Medium Tasks

1. **Build a new feature** - Add "duplicate content" button
2. **Improve performance** - Add pagination to content list
3. **Add analytics** - Track which AI models users use most
4. **Improve UX** - Add keyboard shortcuts (Cmd+S to save)

### Advanced Tasks

1. **Add a new AI provider** - Integrate a new AI model
2. **Add a new social platform** - Implement Bluesky publishing
3. **Optimize database** - Add indexes to slow queries
4. **Refactor a complex component** - Break down large files

---

## ✅ Checklist: Ready to Code?

By the end of Week 1, you should be able to:

- [ ] Run the app locally (frontend + backend)
- [ ] Create an account and log in
- [ ] Make a simple API call in the frontend
- [ ] Create a simple API endpoint in the backend
- [ ] Query the database with psycopg2
- [ ] Understand how JWT authentication works
- [ ] Read and understand an existing route file
- [ ] Make a small code change and test it locally
- [ ] Push code to GitHub and see it deploy

If you can check all these boxes, you're ready to start contributing! 🚀

---

**Welcome to the team! We're excited to have you.** 🎉

Questions? Ping @senior-dev-name in Slack or open a GitHub Discussion.

Happy coding! 💻
