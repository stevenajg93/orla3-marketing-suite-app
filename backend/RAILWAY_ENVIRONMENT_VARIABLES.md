# Railway Environment Variables - Complete Setup

## Overview
This document lists ALL environment variables needed for the Orla³ Marketing Suite backend on Railway.

---

## ✅ REQUIRED - Already Configured

These should already be in Railway:

```bash
# Database (auto-injected by Railway)
DATABASE_URL=postgresql://...

# AI Services
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Image Search
UNSPLASH_ACCESS_KEY=...

# GCP (Vertex AI + Cloud Storage)
GCP_PROJECT_ID=gen-lang-client-0902837589
GCP_CLIENT_ID=...
GCP_CLIENT_SECRET=...
GCP_REFRESH_TOKEN=...
GCS_BUCKET_NAME=gen-lang-client-0902837589-brand-assets

# Gemini API
GEMINI_API_KEY=...
```

---

## 🆕 ADD THESE NOW - Cloud Storage OAuth Tokens

### Google Drive
```bash
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN=YOUR_GOOGLE_REFRESH_TOKEN
```

### Microsoft OneDrive
```bash
ONEDRIVE_CLIENT_ID=YOUR_ONEDRIVE_CLIENT_ID
ONEDRIVE_CLIENT_SECRET=YOUR_ONEDRIVE_CLIENT_SECRET
ONEDRIVE_REFRESH_TOKEN=<YOUR_ONEDRIVE_REFRESH_TOKEN_HERE>
```

### Dropbox
```bash
DROPBOX_APP_KEY=YOUR_DROPBOX_APP_KEY
DROPBOX_APP_SECRET=YOUR_DROPBOX_APP_SECRET
DROPBOX_REFRESH_TOKEN=YOUR_DROPBOX_REFRESH_TOKEN
```

---

## 🔐 SECURITY - Add These for Multi-Tenant Auth

### JWT Authentication
```bash
# Generate with: openssl rand -hex 32
JWT_SECRET=<generate_random_32_byte_hex_string>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

### Application URLs
```bash
FRONTEND_URL=https://orla3-marketing-suite.vercel.app
BACKEND_URL=https://orla3-backend.up.railway.app
```

### Email Service (Resend)
```bash
# Get from: https://resend.com/api-keys
# Free tier: 3,000 emails/month, 100 emails/day
RESEND_API_KEY=re_...
FROM_EMAIL=noreply@orla3.com
```

> **Note**: To use email verification, you need to:
> 1. Sign up at https://resend.com
> 2. Get your API key from https://resend.com/api-keys
> 3. Add your domain or use Resend's test domain for development
> 4. Configure FROM_EMAIL to match your verified domain

---

## 📝 Optional - Social Media (If Needed)

These are in .env.example but not currently used in multi-tenant architecture:

```bash
# Stripe (if implementing billing)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Social Media Platforms
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
WORDPRESS_SITE_URL=
WORDPRESS_APP_PASSWORD=
TUMBLR_CONSUMER_KEY=
TUMBLR_CONSUMER_SECRET=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=
INSTAGRAM_CLIENT_ID=
INSTAGRAM_CLIENT_SECRET=
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
```

---

## 🚀 How to Add Variables to Railway

### Option 1: Railway Dashboard (Recommended)
1. Go to: https://railway.app/dashboard
2. Select your project
3. Click on your backend service
4. Go to **"Variables"** tab
5. Click **"+ New Variable"**
6. Copy/paste each variable name and value
7. Click **"Deploy"** when done

### Option 2: Railway CLI
```bash
railway variables set GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
railway variables set GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET"
railway variables set GOOGLE_REFRESH_TOKEN="1//03fso22qjmuvd..."
# ... repeat for all variables
```

---

## ✅ Verification Checklist

After adding variables, verify:

- [ ] All cloud storage tokens added (Google Drive, OneDrive, Dropbox)
- [ ] JWT_SECRET generated and added
- [ ] FRONTEND_URL and BACKEND_URL updated to production URLs
- [ ] Railway service redeployed successfully
- [ ] Check logs for any missing environment variable errors

---

## 🔄 Token Refresh Schedule

**Important**: OAuth tokens expire and need refreshing:

- **Google Drive Access Token**: 1 hour (auto-refresh with refresh token)
- **OneDrive Access Token**: 1 hour (auto-refresh with refresh token)
- **Dropbox Access Token**: 4 hours (auto-refresh with refresh token)
- **Refresh Tokens**: Long-lived (months/years, stored in database per-user)

The backend will automatically refresh access tokens using refresh tokens when needed.

---

## 🆘 Troubleshooting

### "Invalid client" error
- Double-check CLIENT_ID and CLIENT_SECRET are correct
- Ensure no extra spaces or line breaks in long tokens

### "Redirect URI mismatch"
- Add production callback URLs to each provider:
  - Google: https://console.cloud.google.com/apis/credentials
  - Azure: https://portal.azure.com (App Registrations)
  - Dropbox: https://www.dropbox.com/developers/apps

### Tokens not working
- Regenerate tokens using the provided scripts:
  - `python3 get_google_drive_token.py`
  - `python3 get_onedrive_token.py`
  - `python3 get_dropbox_token.py`
