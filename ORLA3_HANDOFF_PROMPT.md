# ORLA3 Marketing Suite - Complete Handoff Prompt for Future Claude

## 🎯 PROJECT MISSION

You are building **ORLA3 Marketing Suite** - a complete, autonomous content operations platform for a videography/creative agency that runs the entire marketing lifecycle from a single command center.

### Core Mission Statement
Create a deterministic, terminal-driven marketing automation system that executes:
**Brief → Draft → Prime → Publish → Social → Ads → Analytics → Refresh/Boost → CRM Sync**

This is NOT just a content generator - it's a **full-scale digital asset management system** combined with **multi-platform publishing** and **team collaboration**.

---

## 🏗️ COMPLETE SYSTEM ARCHITECTURE

### 1. CONTENT CREATION ENGINE
- **AI-Generated Content**: Blogs (1500+ words), social posts, carousels (7 slides), video scripts, ad copy
- **SEO Optimization**: Entity extraction, internal linking, schema markup, meta tags
- **Brand Voice Enforcement**: Vector similarity matching (≥0.90 cosine) against brand centroid
- **UK English**: All content must use British spelling and grammar

### 2. MULTI-PLATFORM PUBLISHING (9 Platforms)
Publish to ALL of these with platform-specific optimization:
1. **WordPress** - Blogs, long-form content (REST API)
2. **YouTube** - Video uploads, descriptions, thumbnails, chapters (YouTube Data API v3)
3. **LinkedIn** - Posts, articles, carousels, company pages (LinkedIn API)
4. **X/Twitter** - Tweets, threads, media (X API v2)
5. **Instagram** - Posts, stories, reels, carousels (Meta Graph API)
6. **Facebook** - Posts, videos, pages, groups (Meta Graph API)
7. **TikTok** - Short videos, captions, hashtags (TikTok API)
8. **Reddit** - Community posts, discussions (Reddit API)
9. **Tumblr** - Blog posts, media (Tumblr API)

**Platform Adaptation Rules:**
- Auto-resize images/videos to platform specs (aspect ratios, file sizes)
- Adjust character limits (Twitter 280, LinkedIn 3000, etc.)
- Generate platform-appropriate hashtags
- Optimal posting times per platform
- Track post IDs for idempotent updates (no duplicates on rerun)

### 3. ENGAGEMENT & COMMUNITY MANAGEMENT
- **Comment Monitoring**: Fetch comments from ALL platforms via APIs
- **AI-Assisted Replies**: Generate brand-voice responses, human approval queue
- **Sentiment Analysis**: Score comments (positive/neutral/negative), priority flagging
- **Auto-Responder**: Rules-based replies for FAQs, common questions
- **Engagement Metrics**: Reply rates, response times, sentiment trends

### 4. COMPETITIVE INTELLIGENCE
- **Competitor Monitoring**: Track 10+ competitor profiles across platforms
- **Content Analysis**: What they post, when they post, engagement rates
- **Performance Benchmarking**: Compare your metrics vs theirs
- **Gap Analysis**: Topics they cover that you don't
- **Trend Detection**: Emerging keywords, formats, viral patterns
- **Alert System**: Notify when competitors launch major campaigns

### 5. DIGITAL ASSET MANAGEMENT (DAM)
**Full media library for videography agency:**
- **Raw Footage**: Organize by shoot date, client, project, location
- **Work-in-Progress**: Edit timelines, versions, review states
- **Final Deliverables**: Client-approved exports, branded outputs
- **Brand Assets**: Logos (all formats), color palettes, typography, templates
- **Audio Library**: Music, SFX, voiceovers
- **Documents**: Scripts, briefs, contracts, storyboards, shot lists

**Features Required:**
- Upload/download via UI and API
- Smart search (text, tags, visual similarity using vector embeddings)
- Version control (track changes, rollback to previous versions)
- Role-based access (admin, editor, designer, client view-only)
- Project folders (Client Name → Campaign → Assets)
- In-app commenting (frame-accurate video feedback)
- Client upload portal (for raw files and feedback)
- Automatic thumbnail generation for videos
- Metadata extraction (resolution, duration, codec, etc.)

### 6. TEAM COLLABORATION
- **User Roles**: Admin, Editor, Designer, Client, Viewer
- **Approval Workflows**: Draft → Review → Approved → Scheduled → Published
- **Content Calendar**: Visual timeline, drag-and-drop scheduling
- **Notifications**: Tasks due, assets uploaded, comments added, approvals needed
- **Project Dashboards**: Progress tracking per client/campaign
- **Time Tracking**: Editor hours, render times for billing

### 7. ANALYTICS & OPTIMIZATION
- **Data Sources**: Google Analytics 4, Google Search Console, platform-native analytics
- **Nightly Ingestion**: Automated data pull at 02:30 Europe/London
- **KPI Tracking**: Traffic, engagement, conversions, revenue impact
- **Content Refresh Detection**: Find posts ranking 8-15 in SERP with growth potential
- **Auto-Boost**: Suggest actions (add FAQ, internal links, expand E-E-A-T, new schema)
- **A/B Testing**: Test headlines, CTAs, thumbnails

### 8. CRM & CAMPAIGN MANAGEMENT
- **Contact Database**: Lightweight CRM linking contacts ↔ campaigns ↔ content
- **Engagement Tracking**: Who opened/clicked/commented on what
- **Segmentation**: Tags, sources, last touch date
- **Next Actions**: AI-suggested follow-ups per contact
- **Campaign Association**: Link content to active campaigns

---

## 🧩 SUBSYSTEM ARCHITECTURE (12 Total)

### **Subsystem A: Draft Generation** ✅ IMPLEMENTED
- **Status**: DONE - backend/routes/draft.py exists
- **Function**: Generate 1500+ word SEO-optimized blog articles
- **Input**: keyword, search_intent, outline, entities, competitor_notes, brand_tone_rules
- **Output**: JSON with title, slug, meta tags, body_md, CTA, sources
- **Model**: Claude Opus 3 (upgrade to Sonnet 4.5 later)

### **Subsystem B: AI Primer** ❌ TO BUILD
- **Function**: Convert HTML/Markdown into AI-search primers
- **Output**: summary, key_takeaways (5-8), faq (4-6 Q&A), sources

### **Subsystem C: Carousel Generator** ❌ TO BUILD
- **Function**: Create 7-slide carousels for LinkedIn/Instagram
- **Slides**: HOOK, CONTEXT, INSIGHT_1, INSIGHT_2, INSIGHT_3, HOW_TO, CTA

### **Subsystem D: Brand Voice Enforcer** ❌ TO BUILD
- **Function**: Rewrite text to match brand centroid (≥0.90 cosine similarity)

### **Subsystem E: Analytics Refresher** ❌ TO BUILD
- **Function**: Detect posts ranking 8-15, suggest refresh actions
- **Trigger**: Nightly job at 02:30 Europe/London

### **Subsystem F: Paid Ads Manager** ❌ TO BUILD
- **Function**: Generate ad variants for Meta, LinkedIn, X

### **Subsystem G: CRM Assistant** ❌ TO BUILD
- **Function**: Link contacts ↔ campaigns ↔ content, suggest next actions

### **Subsystem H: Multi-Platform Publisher** ❌ TO BUILD
- **Function**: Publish to 9 platforms with platform-specific optimization

### **Subsystem I: Comment & Reply Manager** ❌ TO BUILD
- **Function**: Fetch comments, analyze sentiment, generate AI replies

### **Subsystem J: Competitor Monitor** ❌ TO BUILD
- **Function**: Track competitor content, benchmark performance

### **Subsystem K: Media Asset Manager (DAM)** ❌ TO BUILD
- **Function**: Upload, organize, search media files
- **Storage**: Cloudflare R2 or AWS S3

### **Subsystem L: Team Collaboration** ❌ TO BUILD
- **Function**: User roles, approval workflows, notifications

---

## 📁 CURRENT PROJECT STATE

### Location
~/Desktop/Marketing suite app/orla3-automation/orla3/

### What's Working
✅ Next.js frontend on localhost:3000  
✅ Dashboard UI complete  
✅ FastAPI scaffolded (backend/main.py + routes/draft.py)  
✅ Subsystem A implemented  
✅ Dependencies installed  
✅ Git initialized  

### What's Missing
❌ Backend NOT running (no process on port 8000)  
❌ WordPress credentials not in .env.local  
❌ Supabase not configured  
❌ Social platform API keys missing  
❌ 11 subsystems not built (B-L)  
❌ No E2E flow working  
❌ Media storage not implemented  
❌ No authentication  

---

## 👤 USER PROFILE: Steven

### Technical Skills
- **Interface**: Terminal (bash/zsh) on macOS
- **Style**: "Vibe coder" - needs step-by-step instructions
- **Needs**: One command per message, clear explanations, API setup guidance

### Environment
- **OS**: macOS (M-series)
- **Location**: Graça, Lisbon, PT
- **Timezone**: Europe/London
- **Shell**: zsh

---

## 🔑 API CREDENTIALS NEEDED

### Have
✅ Anthropic API Key

### Need
❌ WordPress (site URL, username, app password)
❌ Supabase (project URL, anon key, service role key)
❌ YouTube Data API v3
❌ LinkedIn API
❌ X/Twitter API
❌ Meta (Facebook/Instagram)
❌ TikTok API
❌ Reddit API
❌ Tumblr API
❌ Google Analytics 4
❌ Google Search Console
❌ Cloudflare R2

---

## 🎯 SUCCESS CRITERIA

### Phase 1: Core Flow
- [ ] Terminal command generates draft
- [ ] Draft displays in dashboard
- [ ] Draft publishes to WordPress
- [ ] Idempotent updates (no duplicates)

### Phase 2: Multi-Platform
- [ ] Publish to LinkedIn, X, Instagram
- [ ] Platform-specific formatting
- [ ] Content calendar working

### Phase 3: Analytics
- [ ] Nightly analytics ingestion
- [ ] Dashboard shows KPI deltas
- [ ] Refresh queue detects 8-15 rank posts

### Phase 4: DAM
- [ ] Upload video file
- [ ] Media library with thumbnails
- [ ] Smart search working
- [ ] Role-based access

### Phase 5: Full Automation
- [ ] Nightly jobs run automatically
- [ ] System stable 7+ days

---

## 🚀 BUILD ORDER

### Sprint 1 (Week 1): E2E Flow
1. Start FastAPI backend
2. Add WordPress credentials
3. Build Subsystem B (AI Primer)
4. Connect draft → primer → WordPress
5. Test terminal to WordPress flow

### Sprint 2 (Week 2): Multi-Platform
6. Set up Supabase schema
7. Get LinkedIn + X API keys
8. Build Subsystem H (Publisher)
9. Test 3-platform publishing

### Sprint 3 (Week 3): Analytics
10. Get GA4 + GSC keys
11. Build Subsystem E (Analytics)
12. Build Subsystem I (Comments)
13. Set up nightly cron

### Sprint 4 (Week 4): DAM
14. Set up Cloudflare R2
15. Build Subsystem K (Media)
16. Add thumbnail generation
17. Build media library UI

### Sprint 5 (Week 5): Team
18. Add Supabase Auth
19. Build Subsystem L (Collaboration)
20. Build approval workflows
21. Add content calendar

### Sprint 6-8: Complete remaining subsystems and deploy

---

## 🛠️ TECHNICAL NOTES

### API Responses
- All AI endpoints return JSON only
- Retry once on invalid JSON
- Use Pydantic validation

### Idempotency
- WordPress: Check slug before creating
- Social: Hash {platform, text, url, day}
- Media: Check file hash before upload

### Brand Voice
- Store centroid in Qdrant/FAISS
- Target ≥0.90 cosine similarity
- Rules in lib/context/orla3-brand.ts

### Scheduling
- Use node-cron (installed)
- Run at 02:30 Europe/London
- Redis for job queues

### Database Schema (Supabase)
Tables: posts, media, jobs, users, comments, competitors, analytics, campaigns, contacts

### Rate Limits
- Claude: 50/min (Opus), 100/min (Sonnet)
- YouTube: 10k units/day
- LinkedIn: 100/day
- Twitter: Varies by tier
- Meta: 200/hour

---

## 📋 CLAUDE RESPONSE FORMAT

When Steven pastes this:

1. **Acknowledge** - Confirm full understanding
2. **Assess** - Check current state
3. **Identify blocker** - What's preventing progress
4. **ONE command** - Single terminal command
5. **Expected outcome** - What success looks like
6. **Next step** - What comes after

---

## 🎓 COMMUNICATION WITH STEVEN

- One command per message
- Explain before the command
- Show expected output
- API setup: exact URLs, step-by-step
- Debug collaboratively
- Celebrate wins with ✅
- Use emojis for scanning (🚀 ✅ ❌ 🔧 📊)

---

## ✅ READY TO USE

Save this file and paste into any future Claude conversation to restore full context!
