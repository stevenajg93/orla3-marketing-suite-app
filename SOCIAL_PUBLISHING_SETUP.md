# Social Media Publishing Setup Guide

## Overview
The ORLA³ Marketing Suite supports direct publishing to 9 social media platforms through the Social Manager dashboard.

## Platform Status

### ✅ Ready to Configure
- Instagram
- LinkedIn
- Twitter/X
- Facebook
- Tumblr
- WordPress

### 🚧 Video Platforms (Coming Soon)
- TikTok (video upload only)
- YouTube (video upload only)
- Reddit (requires subreddit selection)

---

## Quick Start

### 1. Configure Platform Credentials
Add environment variables to `backend/.env` (local) and Railway dashboard (production).

### 2. Test Configuration
```bash
curl http://localhost:8000/publisher/status
```

### 3. Publish from Social Manager
Go to https://marketing.orla3.com/dashboard/social

---

## Platform Configuration

### Instagram
**Requirements:** Instagram Business Account + Facebook Page

**Environment Variables:**
```bash
INSTAGRAM_ACCESS_TOKEN=your_page_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_business_account_id
```

**Setup:**
1. Go to [Facebook for Developers](https://developers.facebook.com)
2. Create app with Instagram Basic Display
3. Get Page Access Token with `instagram_basic`, `instagram_content_publish` permissions
4. Get Business Account ID from Instagram settings

**Supports:** Single images, carousels

---

### LinkedIn
**Requirements:** LinkedIn OAuth Access Token

**Environment Variables:**
```bash
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_PERSON_URN=urn:li:person:YOUR_ID
```

**Setup:**
1. Create LinkedIn app at https://www.linkedin.com/developers/
2. Get OAuth 2.0 with `w_member_social` scope
3. Get Person URN from profile API

**Supports:** Text posts

---

### Twitter/X
**Requirements:** Twitter Developer Account (Elevated Access)

**Environment Variables:**
```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

**Setup:**
1. Apply at https://developer.twitter.com
2. Request Elevated access
3. Generate API keys and tokens

**Supports:** Text tweets
**Status:** ✅ Credentials configured

---

### Facebook
**Requirements:** Facebook Page + Page Access Token

**Environment Variables:**
```bash
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token
FACEBOOK_PAGE_ID=your_page_id
```

**Setup:**
1. Go to [Facebook for Developers](https://developers.facebook.com)
2. Create app with Pages permissions
3. Get token with `pages_manage_posts` permission

**Supports:** Text posts, images

---

### Tumblr
**Requirements:** Tumblr Blog + OAuth Token

**Environment Variables:**
```bash
TUMBLR_API_KEY=your_consumer_key
TUMBLR_API_SECRET=your_consumer_secret
TUMBLR_ACCESS_TOKEN=your_oauth_token
TUMBLR_BLOG_NAME=yourblogname.tumblr.com
```

**Setup:**
1. Register app at https://www.tumblr.com/oauth/apps
2. Get OAuth credentials
3. Authorize your blog

**Supports:** Text posts, images
**Status:** ✅ API keys configured (needs access token)

---

### WordPress
**Requirements:** WordPress site + Application Password (5.6+)

**Environment Variables:**
```bash
WORDPRESS_SITE_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=your_app_password
```

**Setup:**
1. Go to WordPress Dashboard → Users → Profile
2. Scroll to "Application Passwords"
3. Create new application password
4. Copy generated password

**Supports:** Blog posts
**Status:** ✅ Configured for https://blog.orla3.com

---

## Implementation Details

### Backend Endpoint
**File:** `backend/routes/publisher.py`
**URL:** `POST /publisher/publish`

**Request:**
```json
{
  "platform": "instagram",
  "content_type": "text",
  "caption": "Your post content",
  "image_urls": ["https://..."]
}
```

**Response:**
```json
{
  "success": true,
  "platform": "instagram",
  "post_id": "123456",
  "post_url": "https://instagram.com/p/...",
  "published_at": "2025-11-06T10:00:00Z"
}
```

### Frontend
**File:** `app/dashboard/social/page.tsx`
**Function:** `publishToSocial()`

**Features:**
- Multi-platform selection
- AI caption generation
- Media library integration
- Real-time publishing status
- Success/failure reporting

---

## Testing

### Check Configuration Status
```bash
# Local
curl http://localhost:8000/publisher/status

# Production
curl https://orla3-marketing-suite-app-production.up.railway.app/publisher/status
```

### Test Publishing Flow
1. Go to Social Manager: https://marketing.orla3.com/dashboard/social
2. Select platform(s) with green checkmark
3. Write or generate caption
4. (Optional) Add media from library
5. Click "Post Now"
6. View results

---

## Production Deployment

### Railway Environment Variables
Add to Railway dashboard for production:

```bash
# WordPress (configured)
WORDPRESS_SITE_URL=https://blog.orla3.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=xxxx

# Instagram (to configure)
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=

# LinkedIn (to configure)
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=

# Twitter (configured)
TWITTER_API_KEY=xxxx
TWITTER_API_SECRET=xxxx
TWITTER_ACCESS_TOKEN=xxxx
TWITTER_ACCESS_TOKEN_SECRET=xxxx

# Facebook (to configure)
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=

# Tumblr (partially configured)
TUMBLR_API_KEY=xxxx
TUMBLR_API_SECRET=xxxx
TUMBLR_ACCESS_TOKEN=
TUMBLR_BLOG_NAME=
```

**Note:** Do NOT commit actual credentials. Use Railway UI to set values.

---

## Security Best Practices

- ✅ All credentials stored in environment variables
- ✅ `backend/.env` is gitignored
- ✅ Railway encrypts environment variables
- ✅ Use `.env.example` for templates only
- ⚠️ Never commit API keys/tokens to git
- ⚠️ Rotate credentials if exposed

---

## Troubleshooting

### "Platform not configured" Error
**Solution:** Add required environment variables to `.env` (local) or Railway (production)

### "Failed to post" Error
**Check:**
1. Credentials are correct
2. API tokens haven't expired
3. Platform account has posting permissions
4. Check backend logs for specific error

### WordPress Publishing Issues
**Common Issues:**
- REST API disabled (enable in WordPress settings)
- Site is private (make public or add auth)
- Application password incorrect (regenerate)
- DNS not propagated to blog.orla3.com

---

## Next Steps

1. ✅ WordPress configured and ready
2. Configure Instagram Business Account
3. Set up LinkedIn OAuth
4. Create Facebook Page connection
5. Test publishing to each platform
6. Add credentials to Railway for production

---

**Last Updated:** November 6, 2025
**Version:** 1.0
**Status:** WordPress ready, other platforms pending OAuth setup
