# 🔧 ORLA³ Setup Guide

Complete environment configuration guide for local development and production deployment.

---

## 📋 Prerequisites

- **Node.js** 18+
- **Python** 3.12+
- **PostgreSQL** (local or Railway)
- **Git**

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd orla3-marketing-suite-app
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local and set:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your API keys (see below)

# Start backend server
python main.py
```

Backend will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

---

## 🔑 Environment Variables

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production (Vercel):**
```bash
NEXT_PUBLIC_API_URL=https://orla3-marketing-suite-app-production.up.railway.app
```

### Backend (backend/.env)

#### Required Variables

```bash
# AI Services (REQUIRED)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Database (REQUIRED - auto-injected by Railway in production)
DATABASE_URL=postgresql://user:password@localhost:5432/orla3_db

# Image Search (REQUIRED)
UNSPLASH_ACCESS_KEY=...

# Application URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

#### Optional - Google Drive Integration

```bash
SHARED_DRIVE_ID=
SHARED_DRIVE_NAME=
MARKETING_FOLDER_NAME=Marketing
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

You'll also need to place Google OAuth credentials in:
```
backend/credentials/credentials.json
```

#### Optional - Social Media Publishing

Add credentials for platforms you want to publish to:

```bash
# TikTok
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=

# WordPress
WORDPRESS_SITE_URL=https://yoursite.wordpress.com
WORDPRESS_APP_PASSWORD=

# Tumblr
TUMBLR_CONSUMER_KEY=
TUMBLR_CONSUMER_SECRET=

# Reddit
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=

# Facebook
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=

# Instagram (uses Facebook credentials)
INSTAGRAM_CLIENT_ID=
INSTAGRAM_CLIENT_SECRET=

# YouTube
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=

# Twitter/X
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
```

See `backend/.env.local.example` for detailed setup instructions for each platform.

---

## 🗄️ Database Setup

### Option 1: Use Railway PostgreSQL (Recommended)

1. Create a Railway project
2. Add PostgreSQL service
3. Copy the `DATABASE_URL` from Railway
4. Add to `backend/.env`

### Option 2: Local PostgreSQL

```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb orla3_db

# Run schema
psql orla3_db < backend/schema.sql

# Update .env
DATABASE_URL=postgresql://localhost:5432/orla3_db
```

---

## 🔐 Security Checklist

- [ ] Never commit `.env` or `backend/.env` files
- [ ] Never commit `backend/credentials/*.json` files
- [ ] Use separate credentials for development and production
- [ ] Rotate API keys if accidentally exposed
- [ ] Keep `.gitignore` up to date

### If You Accidentally Commit Secrets:

1. **Immediately rotate all exposed credentials**
2. Remove from git history:
```bash
git rm --cached backend/.env
git rm --cached backend/credentials/*.json
git commit -m "Remove sensitive files"
```
3. Use tools like [git-filter-repo](https://github.com/newren/git-filter-repo) to clean history if needed

---

## 🚢 Production Deployment

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Set environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://orla3-marketing-suite-app-production.up.railway.app
   ```
3. Deploy automatically on push to `main`

### Backend (Railway)

1. Connect GitHub repository to Railway
2. Add PostgreSQL service
3. Add environment variables (Railway auto-injects `DATABASE_URL`)
4. Deploy automatically on push to `main`

**Production URLs:**
- Frontend: https://orla3-marketing-suite-app.vercel.app
- Backend: https://orla3-marketing-suite-app-production.up.railway.app

---

## 🧪 Testing

```bash
# Frontend
npm run lint
npm run build

# Backend
cd backend
pytest  # (if tests are added)
```

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Railway Documentation](https://docs.railway.app/)
- [Vercel Documentation](https://vercel.com/docs)

---

## 🆘 Troubleshooting

### "Module not found" errors
```bash
# Frontend
rm -rf node_modules package-lock.json
npm install

# Backend
pip install -r requirements.txt --upgrade
```

### CORS errors
Check that `NEXT_PUBLIC_API_URL` is set correctly in frontend `.env.local`

### Database connection errors
Verify `DATABASE_URL` format and that PostgreSQL is running

### Google Drive authentication
Ensure `credentials.json` is in `backend/credentials/` directory

---

## 💡 Tips

- Use `.env.local` for local overrides (automatically ignored by git)
- Test API endpoints at http://localhost:8000/docs
- Check backend logs at `backend/backend.log`
- Use Railway CLI for debugging production issues

---

**Questions?** Open an issue on GitHub!
