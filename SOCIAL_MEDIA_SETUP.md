# Social Media Publishing Setup Guide

Complete guide to getting OAuth tokens for all 9 social media platforms.

---

## 🟢 Already Working

### ✅ Twitter/X
**Status:** Fixed OAuth 1.0a implementation
**Credentials:** Already in `.env` (just fixed the code)

### ✅ WordPress
**Status:** Fully functional
**Credentials:** Already configured

---

## 🟡 Ready (Need OAuth Tokens)

### 1️⃣ Instagram Business Account

**Requirements:**
- Instagram Business or Creator account
- Facebook Page connected to Instagram
- Facebook Developer App

**Steps:**

1. **Create Facebook App** (if you don't have one)
   - Go to: https://developers.facebook.com/apps
   - Click "Create App" → "Business" type
   - Add "Instagram Basic Display" product

2. **Connect Instagram Business Account**
   - Settings → Basic → Add Instagram Business Account
   - Link your Instagram account to your Facebook Page

3. **Get Access Token**
   - Go to: https://developers.facebook.com/tools/explorer
   - Select your app
   - Request permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`
   - Click "Generate Access Token"
   - Save the token

4. **Get Instagram Business Account ID**
   ```bash
   curl -X GET "https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_ACCESS_TOKEN"
   ```
   Look for `instagram_business_account` → `id`

5. **Add to Railway Environment:**
   ```
   INSTAGRAM_ACCESS_TOKEN=<your_token>
   INSTAGRAM_BUSINESS_ACCOUNT_ID=<your_id>
   ```

**Test:**
```bash
curl -X POST https://orla3-marketing-suite-app-production.up.railway.app/publisher/publish \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "content_type": "image",
    "caption": "Test post from Orla3!",
    "image_urls": ["https://images.unsplash.com/photo-1516035069371-29a1b244cc32"]
  }'
```

---

### 2️⃣ LinkedIn Personal/Company Page

**Requirements:**
- LinkedIn account or Company Page
- LinkedIn Developer App

**Steps:**

1. **Create LinkedIn App**
   - Go to: https://www.linkedin.com/developers/apps
   - Click "Create app"
   - Fill in app details (name, logo, description)
   - Associate with a LinkedIn Page

2. **Request Permissions**
   - Go to Products tab
   - Request "Share on LinkedIn" and "Sign In with LinkedIn using OpenID Connect"
   - Wait for approval (usually instant for personal accounts)

3. **Get OAuth Tokens**
   - Go to Auth tab
   - Note your `Client ID` and `Client Secret`
   - Add redirect URL: `https://orla3-marketing-suite-app-production.up.railway.app/auth/linkedin/callback`

4. **Generate Access Token** (Manual OAuth Flow)

   Visit this URL (replace CLIENT_ID):
   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://orla3-marketing-suite-app-production.up.railway.app/auth/linkedin/callback&scope=profile%20w_member_social%20openid
   ```

   After authorizing, you'll get a `code` in the URL. Exchange it:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code" \
     -d "code=YOUR_CODE" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=https://orla3-marketing-suite-app-production.up.railway.app/auth/linkedin/callback"
   ```

5. **Get Person URN**
   ```bash
   curl -X GET https://api.linkedin.com/v2/userinfo \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```
   Look for `sub` field → format as `urn:li:person:YOUR_SUB`

6. **Add to Railway Environment:**
   ```
   LINKEDIN_ACCESS_TOKEN=<your_token>
   LINKEDIN_PERSON_URN=urn:li:person:<your_sub>
   ```

**Test:**
```bash
curl -X POST https://orla3-marketing-suite-app-production.up.railway.app/publisher/publish \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "content_type": "text",
    "caption": "Excited to share our latest insights on video marketing! #VideoMarketing #CreativeContent"
  }'
```

---

### 3️⃣ Facebook Page

**Requirements:**
- Facebook Page
- Facebook Developer App

**Steps:**

1. **Create/Use Facebook App** (same as Instagram)
   - Go to: https://developers.facebook.com/apps
   - Use existing app or create new one

2. **Get Page Access Token**
   - Go to: https://developers.facebook.com/tools/explorer
   - Select your app
   - Request permissions: `pages_manage_posts`, `pages_read_engagement`
   - Click "Generate Access Token"
   - Select your Facebook Page
   - Save the token

3. **Get Page ID**
   ```bash
   curl -X GET "https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_ACCESS_TOKEN"
   ```
   Look for your page's `id`

4. **Convert to Long-Lived Token** (lasts 60 days)
   ```bash
   curl -X GET "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
   ```

5. **Add to Railway Environment:**
   ```
   FACEBOOK_PAGE_ACCESS_TOKEN=<your_long_lived_token>
   FACEBOOK_PAGE_ID=<your_page_id>
   ```

**Test:**
```bash
curl -X POST https://orla3-marketing-suite-app-production.up.railway.app/publisher/publish \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "facebook",
    "content_type": "text",
    "caption": "New blog post: How to find the perfect videographer for your project!"
  }'
```

---

### 4️⃣ Reddit

**Requirements:**
- Reddit account
- Reddit App

**Steps:**

1. **Create Reddit App**
   - Go to: https://www.reddit.com/prefs/apps
   - Scroll to "developed applications"
   - Click "create another app..."
   - Select "script" type
   - Redirect URI: `http://localhost:8080`
   - Note your `client_id` (under app name) and `client_secret`

2. **Get Access Token**
   ```bash
   curl -X POST https://www.reddit.com/api/v1/access_token \
     -u "YOUR_CLIENT_ID:YOUR_CLIENT_SECRET" \
     -d "grant_type=password&username=YOUR_USERNAME&password=YOUR_PASSWORD"
   ```

3. **Add to Railway Environment:**
   ```
   REDDIT_CLIENT_ID=<your_client_id>
   REDDIT_CLIENT_SECRET=<your_client_secret>
   REDDIT_ACCESS_TOKEN=<your_token>
   REDDIT_USERNAME=<your_username>
   ```

**Note:** Reddit posts require specifying a subreddit. Update the publish endpoint to accept `subreddit` parameter.

---

### 5️⃣ Tumblr

**Requirements:**
- Tumblr account
- Tumblr blog

**Steps:**

1. **Register Tumblr App**
   - Go to: https://www.tumblr.com/oauth/apps
   - Click "Register application"
   - Fill in details
   - Note `OAuth Consumer Key` and `Secret Key`

2. **Get OAuth Token** (use OAuth 1.0a flow)
   - Use a library like `python-tumblpy` or manual OAuth flow
   - Or use: https://api.tumblr.com/console

3. **Add to Railway Environment:**
   ```
   TUMBLR_API_KEY=<consumer_key>
   TUMBLR_API_SECRET=<secret_key>
   TUMBLR_ACCESS_TOKEN=<oauth_token>
   TUMBLR_BLOG_NAME=<yourblog.tumblr.com>
   ```

---

## 🔵 Video Platforms (Coming Soon)

### 🚧 TikTok
**Status:** Requires video upload flow
**Why delayed:** Text/image posts not supported on TikTok

### 🚧 YouTube
**Status:** Requires video upload flow
**Why delayed:** YouTube is video-only platform

---

## ✅ Quick Setup Checklist

Once you have the tokens:

1. **Add tokens to Railway:**
   - Railway Dashboard → Your Project → Variables
   - Add each environment variable
   - Railway will auto-redeploy

2. **Verify configuration:**
   ```bash
   curl https://orla3-marketing-suite-app-production.up.railway.app/publisher/status-all
   ```

3. **Test publishing:**
   ```bash
   curl -X POST https://orla3-marketing-suite-app-production.up.railway.app/publisher/publish \
     -H "Content-Type: application/json" \
     -d '{
       "platform": "linkedin",
       "content_type": "text",
       "caption": "Test post from Orla3 Marketing Suite!"
     }'
   ```

---

## 🛟 Troubleshooting

**"Token expired" error:**
- Instagram/Facebook: Tokens expire after 60 days - regenerate
- LinkedIn: Tokens expire after 60 days - regenerate
- Twitter: Tokens don't expire (unless revoked)

**"Insufficient permissions" error:**
- Check you requested all required permissions
- For Instagram: Ensure account is Business/Creator type
- For LinkedIn: Ensure "Share on LinkedIn" is approved

**"Invalid credentials" error:**
- Verify all 4 credentials for Twitter (API Key, API Secret, Access Token, Access Token Secret)
- Verify tokens haven't been regenerated (old tokens become invalid)

---

## 📞 Support

For platform-specific help:
- **Instagram:** https://developers.facebook.com/docs/instagram-api
- **LinkedIn:** https://docs.microsoft.com/en-us/linkedin/
- **Facebook:** https://developers.facebook.com/docs/pages
- **Twitter:** https://developer.twitter.com/en/docs/twitter-api
- **Reddit:** https://www.reddit.com/dev/api
- **Tumblr:** https://www.tumblr.com/docs/en/api/v2

---

**Last Updated:** November 7, 2025
