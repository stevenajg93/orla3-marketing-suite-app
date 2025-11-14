# ORLA³ MARKETING SUITE - COMPLETE SOCIAL MEDIA IMPLEMENTATION PLAN

**Status:** IN PROGRESS
**Start Date:** November 14, 2025
**Target Completion:** December 15, 2025 (4 weeks)
**Goal:** Transform from 60% complete to 100% production-ready social media management platform

---

## 🎯 EXECUTIVE SUMMARY

### Current State (60% Complete)
- ✅ OAuth authentication: 8/8 platforms working
- ✅ Publishing: 5/8 platforms operational (Instagram, LinkedIn, Facebook, X, Tumblr, WordPress)
- ✅ Competitor analysis: Fully operational with Perplexity AI + Claude
- ⚠️ Scheduling: UI exists, NO automation
- ⚠️ Engagement: UI mockups, NO API integration
- ❌ Post Discovery: NOT implemented
- ❌ Video platforms: NOT implemented (TikTok, YouTube)

### Target State (100% Complete)
- ✅ Automated scheduling with background worker
- ✅ Real-time comment fetching from all platforms
- ✅ AI-powered engagement with real API integration
- ✅ Post discovery (search relevant conversations)
- ✅ Complete platform support (8/8 with all media types)
- ✅ Calendar-integrated workflow
- ✅ Character limit validation
- ✅ Real-time monitoring and auto-replies

---

## 📊 CURRENT PLATFORM SUPPORT MATRIX

| Platform | Text | Image | Carousel | Video | Limits | Comments | Discovery | Schedule |
|----------|------|-------|----------|-------|--------|----------|-----------|----------|
| **Instagram** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **LinkedIn** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Facebook** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **X/Twitter** | ✅ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ |
| **Tumblr** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **WordPress** | ✅ | ❌ | ❌ | ❌ | ❌ | N/A | N/A | ❌ |
| **TikTok** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **YouTube** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Reddit** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Legend:** ✅ Working | ⚠️ Frontend Only | ❌ Not Implemented

---

## 🔴 CRITICAL GAPS IDENTIFIED

### 1. SCHEDULING AUTOMATION - NOT IMPLEMENTED
**Problem:**
- UI accepts schedule dates ✅
- Database stores scheduled posts ✅
- **NO CRON JOB OR WORKER TO AUTO-PUBLISH** ❌

**Impact:** Users can't schedule posts - defeats primary use case

**Files Affected:**
- `backend/schema.sql` - content_calendar table exists
- `app/dashboard/social/page.tsx` - schedule UI present
- `backend/routes/publisher.py` - publish endpoint exists
- **MISSING:** Background worker

### 2. ENGAGEMENT FEATURES - UI MOCKUPS ONLY
**Problem:**
- Beautiful UI with Inbox/Discovery/Settings tabs ✅
- Backend AI comment reply endpoint exists (`/comments/reply`) ✅
- **FRONTEND USES FAKE DATA, DOESN'T CALL BACKEND** ❌

**Impact:** Engagement tab is a demo, not functional

**Files Affected:**
- `app/dashboard/social/page.tsx` line 615 - `generateAIReplies()` uses mockReplies
- `app/dashboard/social/page.tsx` line 108 - `mockComments` array
- `backend/routes/comments.py` - endpoint exists but unused

### 3. POST DISCOVERY - NOT IMPLEMENTED
**Problem:**
- UI has search bar + discovery feed ✅
- **NO BACKEND ENDPOINT, SHOWS FAKE POSTS** ❌

**Impact:** Can't find relevant posts to engage with

**Files Affected:**
- `app/dashboard/social/page.tsx` line 630 - `searchRelevantPosts()` uses setTimeout
- **MISSING:** `/social/discover` backend endpoint

### 4. CHARACTER LIMITS - NOT ENFORCED
**Problem:**
- Frontend warns for X (280 chars) ✅
- **Backend doesn't validate** ❌

**Impact:** Posts may fail or get truncated

**Platform Limits:**
- X/Twitter: 280 characters
- Instagram: 2,200 characters
- LinkedIn: 3,000 characters
- Facebook: 63,206 characters
- Reddit: 40,000 characters (post), 10,000 (comment)
- Tumblr: Unlimited
- WordPress: Unlimited

### 5. VIDEO PLATFORMS - NOT IMPLEMENTED
**Problem:**
- OAuth connected ✅
- **Publishing returns "not implemented" errors** ❌

**Impact:** Can't use TikTok, YouTube, Reddit

**Platforms:**
- TikTok: Needs Direct Post API (video upload)
- YouTube: Needs resumable upload (YouTube Data API v3)
- Reddit: Needs subreddit selector + post submission

---

## 📋 7-PHASE IMPLEMENTATION PLAN

### **PHASE 1: AUTOMATED SCHEDULING (3-4 days) 🔴 CRITICAL**

**Goal:** Background worker auto-publishes scheduled posts

**Tasks:**
1. ✅ Add APScheduler to requirements.txt
2. ✅ Create `backend/scheduler.py` with APScheduler setup
3. ✅ Create `backend/workers/post_scheduler.py`
   - Check `content_calendar` every minute for due posts
   - Fetch post details from `content_library` or calendar metadata
   - Call `/publisher/publish` with platform credentials
   - Update calendar event status (scheduled → published/failed)
4. ✅ Add character limit validation to `backend/routes/publisher.py`
   - Validate before API calls
   - Return 400 error with platform limits
5. ✅ Integrate scheduler into `backend/main.py` startup event
6. ✅ Add error handling + retry logic (3 retries with exponential backoff)
7. ✅ Add logging for scheduled posts

**Files to Create:**
- `backend/scheduler.py` (APScheduler config)
- `backend/workers/post_scheduler.py` (scheduled post processor)
- `backend/utils/validators.py` (character limit validators)

**Files to Modify:**
- `backend/requirements.txt` (add APScheduler==3.10.4)
- `backend/main.py` (start scheduler on startup)
- `backend/routes/publisher.py` (add validation)

**Testing:**
1. Create calendar event with scheduled_date = now + 2 minutes
2. Verify worker picks it up and publishes
3. Check calendar status updates to 'published'
4. Test character limit rejection (post 300 char to X)

**API Endpoints:**
- No new endpoints needed

**Database Changes:**
- No schema changes needed (calendar table already has scheduled_date)

---

### **PHASE 2: ENGAGEMENT FEATURES (4-5 days) 🔴 CRITICAL**

**Goal:** Replace UI mockups with real platform API integration

**Tasks:**

#### 2A. Instagram Comment Fetching
1. ✅ Add endpoint: `GET /social/comments/instagram`
2. ✅ Use Instagram Graph API: `/{media-id}/comments`
3. ✅ Require scope: `instagram_manage_comments`
4. ✅ Return: comment_id, username, text, timestamp, media_id

#### 2B. Facebook Comment Fetching
1. ✅ Add endpoint: `GET /social/comments/facebook`
2. ✅ Use Facebook Graph API: `/{post-id}/comments`
3. ✅ Require scope: `pages_manage_engagement`
4. ✅ Return: comment_id, from (user), message, created_time

#### 2C. Twitter Mentions Fetching
1. ✅ Add endpoint: `GET /social/comments/twitter`
2. ✅ Use Twitter API v2: `/tweets/search/recent?query=@username`
3. ✅ Require scope: `tweet.read`
4. ✅ Return: tweet_id, author_id, text, created_at

#### 2D. Frontend Integration
1. ✅ Replace `mockComments` with real API call in `app/dashboard/social/page.tsx`
2. ✅ Replace `generateAIReplies()` with fetch to `/comments/reply`
3. ✅ Add loading states for comment fetching
4. ✅ Add error handling (API rate limits, no permissions)

#### 2E. AI Reply Integration
1. ✅ Connect frontend "Generate Reply" button to `/comments/reply` endpoint
2. ✅ Pass: comment text, platform, brand context
3. ✅ Display AI-generated reply in textarea
4. ✅ Allow user to edit before posting

**Files to Create:**
- `backend/routes/social_engagement.py` (comment fetching endpoints)

**Files to Modify:**
- `app/dashboard/social/page.tsx` (remove mocks, add real API calls)
- `backend/routes/comments.py` (ensure reply endpoint is working)

**Testing:**
1. Connect Instagram account, post a photo, add comment
2. Open Engage tab → Inbox, verify comment appears
3. Click "Generate Reply", verify AI response
4. Test Facebook, Twitter comments

**API Endpoints:**
- `GET /social/comments/instagram` - Fetch Instagram comments
- `GET /social/comments/facebook` - Fetch Facebook comments
- `GET /social/comments/twitter` - Fetch Twitter mentions
- `POST /comments/reply` - Already exists, just connect frontend

**Database Changes:**
- No schema changes needed

**OAuth Scope Requirements:**
- Instagram: `instagram_manage_comments` (check if we have this)
- Facebook: `pages_manage_engagement` (check if we have this)
- Twitter: `tweet.read` (check if we have this)

---

### **PHASE 3: POST DISCOVERY (3-4 days) 🟡 HIGH**

**Goal:** Search relevant posts by keywords to engage with

**Tasks:**

#### 3A. Twitter Search API
1. ✅ Add endpoint: `POST /social/discover/twitter`
2. ✅ Use Twitter API v2: `/tweets/search/recent`
3. ✅ Parameters: query (keywords/hashtags), max_results (10-100)
4. ✅ Return: tweet_id, author, text, created_at, engagement metrics

#### 3B. Reddit Search API
1. ✅ Add endpoint: `POST /social/discover/reddit`
2. ✅ Use Reddit API: `/r/{subreddit}/search` or `/search`
3. ✅ Parameters: query, subreddit (optional), sort (relevance/hot/new)
4. ✅ Return: post_id, author, title, selftext, score, num_comments

#### 3C. LinkedIn Search (if available)
1. ⚠️ Check if LinkedIn API supports post search (likely not public)
2. ✅ If not: Use Perplexity AI fallback to scrape LinkedIn posts
3. ✅ Return: post_url, author, content, engagement

#### 3D. Frontend Integration
1. ✅ Replace `mockDiscoveryPosts` with real API call
2. ✅ Replace `searchRelevantPosts()` setTimeout with fetch to `/social/discover`
3. ✅ Add platform selector (Twitter, Reddit, LinkedIn)
4. ✅ Add filters: date range, engagement threshold

**Files to Create:**
- `backend/routes/social_discovery.py` (search endpoints)

**Files to Modify:**
- `app/dashboard/social/page.tsx` (connect discovery tab to API)

**Testing:**
1. Search Twitter for "videography tips"
2. Verify results show recent tweets
3. Search Reddit for "wedding videography"
4. Click "Generate Comment" on discovered post

**API Endpoints:**
- `POST /social/discover/twitter` - Search Twitter posts
- `POST /social/discover/reddit` - Search Reddit posts
- `POST /social/discover/linkedin` - Search LinkedIn (or Perplexity fallback)

**Database Changes:**
- Optional: `discovered_posts` table to cache results

---

### **PHASE 4: COMPLETE ALL PLATFORMS (5-6 days) 🟡 HIGH**

**Goal:** 8/8 platforms fully operational with all media types

**Tasks:**

#### 4A. TikTok Video Upload
1. ✅ Research TikTok Direct Post API (Content Posting API)
2. ✅ Implement video upload flow:
   - Initialize upload session
   - Upload video chunks
   - Publish video post
3. ✅ Update `backend/routes/publisher.py` TikTokPublisher class
4. ✅ Add video file validation (format, size, duration limits)
5. ✅ Test: Upload 15-second video to TikTok

**API Docs:** https://developers.tiktok.com/doc/content-posting-api-get-started/

#### 4B. YouTube Video Upload
1. ✅ Research YouTube Data API v3 resumable upload
2. ✅ Implement upload flow:
   - Create video resource
   - Upload video file (resumable)
   - Set metadata (title, description, tags)
3. ✅ Update `backend/routes/publisher.py` YouTubePublisher class
4. ✅ Add video privacy settings (public/unlisted/private)
5. ✅ Test: Upload video to YouTube channel

**API Docs:** https://developers.google.com/youtube/v3/guides/uploading_a_video

#### 4C. Reddit Subreddit Selection
1. ✅ Add UI subreddit selector in `app/dashboard/social/page.tsx`
2. ✅ Update RedditPublisher to accept subreddit parameter
3. ✅ Implement Reddit post submission (text, link, or image)
4. ✅ Add subreddit validation (must exist, user must have permission)
5. ✅ Test: Post to r/test subreddit

#### 4D. LinkedIn Image Publishing
1. ✅ Research LinkedIn asset registration API
2. ✅ Implement image upload flow:
   - Register upload (get upload URL)
   - Upload image binary
   - Create post with asset URN
3. ✅ Update `backend/routes/publisher.py` LinkedInPublisher class
4. ✅ Test: Post with image to LinkedIn

**API Docs:** https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/images-api

#### 4E. Twitter Media Upload
1. ✅ Research Twitter API v2 media upload
2. ✅ Implement upload flow:
   - Upload media (POST /media/upload)
   - Create tweet with media_ids
3. ✅ Update `backend/routes/publisher.py` TwitterPublisher class
4. ✅ Support images (up to 4) and videos (1)
5. ✅ Test: Tweet with image

**API Docs:** https://developer.twitter.com/en/docs/twitter-api/v1/media/upload-media/overview

**Files to Modify:**
- `backend/routes/publisher.py` (update all 5 publisher classes)
- `app/dashboard/social/page.tsx` (add subreddit selector for Reddit)

**Testing:**
1. Upload video to TikTok (15-sec test video)
2. Upload video to YouTube (30-sec test video)
3. Post to r/test with text + image
4. Post to LinkedIn with image
5. Tweet with 1-4 images

**Database Changes:**
- No schema changes needed

---

### **PHASE 5: CALENDAR INTEGRATION (2-3 days) 🟢 MEDIUM**

**Goal:** Unified workflow - Social Manager → Calendar → Publishing

**Tasks:**

#### 5A. Calendar Publish Button
1. ✅ Add "Publish Now" button to calendar events in `app/dashboard/calendar/page.tsx`
2. ✅ Fetch event details from calendar
3. ✅ Call `/publisher/publish` with event content
4. ✅ Update event status to 'published'

#### 5B. Social Manager → Calendar Integration
1. ✅ When user sets schedule date in Social Manager, save to calendar
2. ✅ Modify `app/dashboard/social/page.tsx` publishToSocial() function:
   - If scheduleDate is set, save to `content_calendar` instead of publishing
   - Store: title, content, platform, scheduled_date, status='scheduled'
3. ✅ Show success message: "Post scheduled for [date]"

#### 5C. Edit Scheduled Posts
1. ✅ Add "Edit" button to calendar events
2. ✅ Open modal with editable content
3. ✅ Update calendar event via `PUT /calendar/events/{id}`

#### 5D. Bulk Actions
1. ✅ Add "Publish All Due" button to calendar
2. ✅ Fetch all events where scheduled_date <= now AND status='scheduled'
3. ✅ Publish each one sequentially
4. ✅ Show progress (5/10 published)

**Files to Modify:**
- `app/dashboard/calendar/page.tsx` (add publish buttons, edit modal)
- `app/dashboard/social/page.tsx` (integrate with calendar on schedule)
- `backend/routes/calendar.py` (ensure update endpoint works)

**Testing:**
1. Schedule post from Social Manager for tomorrow
2. Verify it appears in calendar
3. Click "Publish Now" from calendar, verify it posts
4. Edit scheduled post content from calendar
5. Schedule 5 posts for now + 1 minute
6. Click "Publish All Due", verify all publish

**Database Changes:**
- Potentially add `content_json` column to `content_calendar` to store full post content

---

### **PHASE 6: REAL-TIME MONITORING (3-4 days) 🟢 MEDIUM**

**Goal:** Auto-fetch comments every 15 minutes, optional auto-reply

**Tasks:**

#### 6A. Background Comment Polling
1. ✅ Add APScheduler job to fetch comments every 15 minutes
2. ✅ For each connected platform:
   - Fetch recent comments (last 24 hours)
   - Store in `social_comments` table (new)
   - Flag new comments as 'unread'
3. ✅ Deduplicate comments (don't re-fetch same comment)

#### 6B. User Preferences Table
1. ✅ Create `user_preferences` table:
   - user_id, auto_reply_enabled, auto_reply_platforms (JSONB)
   - comment_polling_interval (default 15 minutes)
2. ✅ Add migration script

#### 6C. Auto-Reply Logic
1. ✅ If auto_reply_enabled = true for platform:
   - Fetch new comments
   - Generate AI reply via `/comments/reply`
   - Post reply automatically
   - Mark comment as 'replied'
2. ✅ Add safety: Only auto-reply to comments with positive/neutral sentiment

#### 6D. Frontend Settings Persistence
1. ✅ Save auto-reply toggle to `user_preferences` table
2. ✅ Load settings on page load
3. ✅ Add "Auto-Reply Settings" modal with per-platform toggles

**Files to Create:**
- `backend/workers/comment_monitor.py` (background polling)
- `backend/schema_updates/009_user_preferences.sql` (new table)
- `backend/schema_updates/010_social_comments.sql` (new table)

**Files to Modify:**
- `backend/scheduler.py` (add comment polling job)
- `app/dashboard/social/page.tsx` (persist settings)
- `backend/routes/user_preferences.py` (new endpoint)

**Testing:**
1. Enable auto-reply for Instagram
2. Post photo, add comment from test account
3. Wait 15 minutes, verify auto-reply appears
4. Disable auto-reply, add another comment
5. Verify no auto-reply

**Database Changes:**
```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    auto_reply_enabled BOOLEAN DEFAULT false,
    auto_reply_platforms JSONB DEFAULT '{}',
    comment_polling_interval INTEGER DEFAULT 15,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE social_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    platform TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    post_id TEXT,
    author TEXT,
    content TEXT,
    sentiment TEXT,
    status TEXT DEFAULT 'unread',
    replied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform, comment_id)
);
```

---

### **PHASE 7: TESTING + DEPLOYMENT (2-3 days) 🔴 CRITICAL**

**Goal:** Verify everything works end-to-end, deploy to production

**Tasks:**

#### 7A. End-to-End Platform Testing
1. ✅ Test Instagram: Publish now, schedule, fetch comments, discover posts
2. ✅ Test LinkedIn: Publish with image, schedule
3. ✅ Test Facebook: Publish now, fetch comments
4. ✅ Test Twitter: Publish with media, fetch mentions, discover posts
5. ✅ Test TikTok: Upload video
6. ✅ Test YouTube: Upload video
7. ✅ Test Reddit: Post to subreddit, discover posts
8. ✅ Test Tumblr: Publish with image
9. ✅ Test WordPress: Publish blog post

#### 7B. Error Handling Testing
1. ✅ Test character limit rejection (post 300 char to X)
2. ✅ Test expired OAuth token (disconnect and retry)
3. ✅ Test API rate limits (spam requests)
4. ✅ Test failed scheduled post (platform down)
5. ✅ Test invalid media (wrong format/size)

#### 7C. Performance Testing
1. ✅ Schedule 50 posts for same time, verify all publish
2. ✅ Fetch 100 comments, verify no timeout
3. ✅ Search 1000 posts, verify pagination works

#### 7D. Documentation Update
1. ✅ Update README.md with new features
2. ✅ Update ORLA3_HANDOFF_PROMPT.md
3. ✅ Create API documentation for new endpoints
4. ✅ Update platform support matrix (all ✅)

#### 7E. Production Deployment
1. ✅ Commit all changes to GitHub
2. ✅ Railway auto-deploys backend
3. ✅ Vercel auto-deploys frontend
4. ✅ Run database migrations on production
5. ✅ Smoke test all features in production

#### 7F. Production Smoke Tests
1. ✅ Create test account on production
2. ✅ Connect all 8 platforms
3. ✅ Schedule 1 post for each platform (now + 5 minutes)
4. ✅ Verify all 8 posts publish successfully
5. ✅ Check logs for errors

**Files to Modify:**
- `README.md` (update platform matrix, add new features)
- `ORLA3_HANDOFF_PROMPT.md` (update architecture version)

**Testing Checklist:**
- [ ] All 8 platforms publish successfully
- [ ] Scheduled posts auto-publish
- [ ] Comments fetched from Instagram/Facebook/Twitter
- [ ] AI replies generated correctly
- [ ] Post discovery returns results
- [ ] Character limits enforced
- [ ] Video uploads work (TikTok, YouTube)
- [ ] Reddit subreddit selection works
- [ ] Calendar publish buttons work
- [ ] Auto-reply settings persist
- [ ] Error handling graceful

---

## 📊 PROGRESS TRACKING

### Overall Completion: 0% (Not Started)

| Phase | Status | Progress | Start Date | End Date |
|-------|--------|----------|------------|----------|
| Phase 1: Scheduling | Not Started | 0% | - | - |
| Phase 2: Engagement | Not Started | 0% | - | - |
| Phase 3: Discovery | Not Started | 0% | - | - |
| Phase 4: Platforms | Not Started | 0% | - | - |
| Phase 5: Calendar | Not Started | 0% | - | - |
| Phase 6: Monitoring | Not Started | 0% | - | - |
| Phase 7: Testing | Not Started | 0% | - | - |

### Key Metrics to Track
- [ ] Scheduled posts auto-publish success rate (target: 99%)
- [ ] Comment fetch latency (target: <2 seconds)
- [ ] AI reply generation success rate (target: 95%)
- [ ] Platform publish success rate per platform (target: 98%)
- [ ] Character limit validation accuracy (target: 100%)

---

## 🚨 RISKS & MITIGATION

### Risk 1: API Rate Limits
**Impact:** High - Could block comment fetching or post discovery
**Mitigation:**
- Implement exponential backoff
- Cache API responses for 15 minutes
- Add rate limit tracking per platform
- Fallback to Perplexity AI for discovery if API limits hit

### Risk 2: OAuth Scope Changes
**Impact:** Medium - Platforms may require additional permissions
**Mitigation:**
- Document all required scopes per platform
- Add scope checking before API calls
- Guide users to re-authorize if scopes missing

### Risk 3: APScheduler on Railway
**Impact:** Medium - Railway may restart workers
**Mitigation:**
- Persistent scheduler state (SQLite or PostgreSQL)
- Idempotent job execution (don't double-publish)
- Add job recovery on startup

### Risk 4: Video Upload Performance
**Impact:** Medium - Large files may timeout
**Mitigation:**
- Implement chunked uploads (TikTok, YouTube)
- Add upload progress tracking
- Set timeout to 10 minutes for video endpoints
- Validate file size before upload (max 100MB)

### Risk 5: Comment Polling Load
**Impact:** Low - Could increase API costs
**Mitigation:**
- Only poll platforms user has connected
- User-configurable polling interval (default 15 min)
- Skip polling if no posts in last 7 days

---

## 📈 SUCCESS CRITERIA

### Must-Have (Launch Blockers)
- [x] Phase 1: Automated scheduling works for all platforms
- [x] Phase 2: Real comments fetched from Instagram, Facebook, Twitter
- [x] Character limit validation enforces platform limits
- [x] All 8 platforms can publish successfully
- [x] Error handling prevents app crashes

### Should-Have (High Value)
- [x] Phase 3: Post discovery works for Twitter, Reddit
- [x] Phase 4: Video uploads work for TikTok, YouTube
- [x] Phase 5: Calendar publish integration complete
- [x] LinkedIn image publishing works
- [x] Twitter media upload works

### Nice-to-Have (Future Enhancement)
- [ ] Phase 6: Real-time comment monitoring with auto-reply
- [ ] Analytics dashboard (post performance tracking)
- [ ] Best time to post recommendations
- [ ] Recurring post schedules
- [ ] Bulk CSV import for scheduled posts

---

## 📝 NOTES & DECISIONS

### Architecture Decisions
1. **APScheduler over Celery:** Simpler setup, no Redis needed, perfect for Railway
2. **Polling over Webhooks:** More reliable, easier to implement, works for all platforms
3. **Perplexity Fallback:** Use for discovery when platform APIs unavailable (LinkedIn)
4. **Character Limits in Backend:** Prevent wasted API calls, better error messages

### Platform-Specific Notes
- **Instagram:** Requires Business/Creator account for publishing
- **TikTok:** Still in review, may not be available immediately
- **LinkedIn:** Image publishing requires asset registration (multi-step)
- **Twitter:** Media upload uses v1.1 API (v2 doesn't support media yet)
- **Reddit:** User must specify subreddit (can't be auto-detected)
- **YouTube:** Videos must pass community guidelines (may be delayed)

### Credit Cost Considerations
- Comment fetch: 0 credits (read-only)
- AI reply generation: 2 credits per reply (same as social caption)
- Post discovery: 1 credit per search
- Scheduled publish: Same cost as immediate publish (per operation type)

---

## 🎯 DEFINITION OF DONE

**Phase 1 Done When:**
- [ ] Schedule post from Social Manager
- [ ] Post auto-publishes at scheduled time
- [ ] Calendar status updates to 'published'
- [ ] Character limit error shows for 300-char X post
- [ ] All 8 platforms respect character limits

**Phase 2 Done When:**
- [ ] Open Engage tab, see real Instagram comments
- [ ] Click "Generate Reply", see AI response from backend
- [ ] Real Facebook comments appear
- [ ] Real Twitter mentions appear
- [ ] No more mockComments or setTimeout in code

**Phase 3 Done When:**
- [ ] Search "videography" on Twitter, see results
- [ ] Search "wedding" on Reddit, see posts
- [ ] Click "Generate Comment" on discovered post
- [ ] No more mockDiscoveryPosts in code

**Phase 4 Done When:**
- [ ] Upload 15-sec video to TikTok successfully
- [ ] Upload 30-sec video to YouTube successfully
- [ ] Post to r/test with text and image
- [ ] Post to LinkedIn with image
- [ ] Tweet with 1-4 images

**Phase 5 Done When:**
- [ ] Schedule post from Social Manager, see in calendar
- [ ] Click "Publish Now" from calendar, post publishes
- [ ] Edit scheduled post content from calendar
- [ ] "Publish All Due" button works

**Phase 6 Done When:**
- [ ] Enable auto-reply toggle, setting persists
- [ ] Add comment to Instagram post, auto-reply appears in 15 min
- [ ] Disable auto-reply, no more auto-replies

**Phase 7 Done When:**
- [ ] All 8 platforms tested end-to-end
- [ ] README.md updated with new features
- [ ] Deployed to production
- [ ] Smoke tests pass in production
- [ ] No critical bugs

---

## 📞 SUPPORT & RESOURCES

### API Documentation Links
- **Instagram Graph API:** https://developers.facebook.com/docs/instagram-api
- **Facebook Graph API:** https://developers.facebook.com/docs/graph-api
- **Twitter API v2:** https://developer.twitter.com/en/docs/twitter-api
- **LinkedIn API:** https://learn.microsoft.com/en-us/linkedin/marketing/
- **TikTok API:** https://developers.tiktok.com/doc/content-posting-api-get-started/
- **YouTube Data API:** https://developers.google.com/youtube/v3
- **Reddit API:** https://www.reddit.com/dev/api/
- **Tumblr API:** https://www.tumblr.com/docs/en/api/v2
- **WordPress API:** https://developer.wordpress.com/docs/api/

### Internal Documentation
- `README.md` - High-level project overview
- `ORLA3_HANDOFF_PROMPT.md` - Complete architecture documentation
- `backend/schema.sql` - Database schema
- `backend/routes/social_auth.py` - OAuth implementation reference

---

**Last Updated:** November 14, 2025
**Next Review:** After Phase 1 completion
**Owner:** Steven Gillespie + Claude (CTO)
