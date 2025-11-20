# Testing Checklist - Code Quality Fixes
**Date:** November 20, 2025
**Commit:** 397cdb1
**Tester:** _____________

---

## Pre-Testing Setup

- [ ] Wait for Vercel deployment to complete (check: https://vercel.com/sgillespie-3759s-projects/orla3-marketing-suite-app)
- [ ] Wait for Railway deployment to complete (check: https://railway.com/project/b5320646-39a5-4267-a1d0-65d72f0f580d)
- [ ] Verify backend health: https://orla3-marketing-suite-app-production.up.railway.app/health
- [ ] Verify frontend loads: https://marketing.orla3.com

---

## Fix #1: Collaboration Endpoint Authentication

### Test 1.1: Unauthorized Access Blocked
- [ ] Open browser console
- [ ] Try to call endpoint without auth:
```javascript
fetch('https://orla3-marketing-suite-app-production.up.railway.app/collab/workflow', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ users: [], content_items: [], action: 'assign_workflow' })
}).then(r => console.log('Status:', r.status))
```
- [ ] **Expected:** HTTP 401 Unauthorized
- [ ] **Actual:** _____________

### Test 1.2: Authorized Access Works
- [ ] Log in to marketing.orla3.com
- [ ] Open browser console
- [ ] Get access token: `localStorage.getItem('access_token')`
- [ ] Try authenticated call:
```javascript
fetch('https://orla3-marketing-suite-app-production.up.railway.app/collab/workflow', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  },
  body: JSON.stringify({
    users: [{
      id: "your-user-id",
      name: "Test User",
      email: "test@example.com",
      org_role: "admin",
      job_function: "editor"
    }],
    content_items: [],
    action: 'assign_workflow'
  })
}).then(r => r.json()).then(console.log)
```
- [ ] **Expected:** HTTP 200 with assignments and notifications
- [ ] **Actual:** _____________

---

## Fix #2: Standardized Error Handling

### Test 2.1: Library Content Creation Error
- [ ] Log in to marketing.orla3.com
- [ ] Open browser console
- [ ] Try to create invalid content (trigger error):
```javascript
fetch('https://orla3-marketing-suite-app-production.up.railway.app/library/content', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  },
  body: JSON.stringify({
    // Missing required fields to trigger error
    title: ""
  })
}).then(r => console.log('Status:', r.status, r.ok))
```
- [ ] **Expected:** r.ok = false (HTTP error status, not HTTP 200)
- [ ] **Actual:** _____________

### Test 2.2: Library Content Creation Success
- [ ] Try to create valid content:
```javascript
fetch('https://orla3-marketing-suite-app-production.up.railway.app/library/content', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  },
  body: JSON.stringify({
    title: "Test Content",
    content_type: "test",
    content: "This is a test",
    status: "draft",
    platform: "Test"
  })
}).then(r => r.json()).then(d => console.log('Success:', d.success, 'Item:', d.item?.id))
```
- [ ] **Expected:** success: true, item with ID returned
- [ ] **Actual:** _____________

---

## Fix #3: GET /content/{id} Endpoint

### Test 3.1: Fetch Single Content Item
- [ ] Go to Media Library page
- [ ] Note any content item ID from the list
- [ ] In console:
```javascript
const itemId = "PASTE_ITEM_ID_HERE";
fetch(`https://orla3-marketing-suite-app-production.up.railway.app/library/content/${itemId}`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
}).then(r => r.json()).then(item => {
  console.log('Title:', item.title);
  console.log('Content length:', item.content?.length);
  console.log('Has full content?', !!item.content);
})
```
- [ ] **Expected:** Full item with content field populated
- [ ] **Actual:** _____________

### Test 3.2: Fetch Non-Existent Item
- [ ] Try fetching invalid ID:
```javascript
fetch('https://orla3-marketing-suite-app-production.up.railway.app/library/content/00000000-0000-0000-0000-000000000000', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
}).then(r => console.log('Status:', r.status))
```
- [ ] **Expected:** HTTP 404 Not Found
- [ ] **Actual:** _____________

---

## Fix #4: Aligned Role Systems

### Test 4.1: Review Role Documentation
- [ ] Open `backend/ROLE_SYSTEM.md`
- [ ] Verify documentation is clear and comprehensive
- [ ] Note: This is architectural - no functional changes to test yet

---

## Fix #5: Blog-to-Social Flow (Most Important!)

### Test 5.1: Create Blog and Send to Social Manager
- [ ] Go to Blog Writer page
- [ ] Click "Auto-Generate" or manually generate a blog
- [ ] Wait for blog to be generated
- [ ] Click "Send to Social Manager" button
- [ ] **Expected:** Redirects to Social Manager with campaign parameter in URL
- [ ] **Actual URL:** _____________

### Test 5.2: Verify Social Manager Loads Blog
- [ ] Check that Social Manager loads
- [ ] **Expected:** Caption field pre-filled with blog content
- [ ] **Actual:** Caption filled? YES / NO
- [ ] **Expected:** URL cleans up (campaign parameter removed)
- [ ] **Actual:** Final URL = /dashboard/social (no params)

### Test 5.3: Cross-Device Support
- [ ] On Device 1: Generate blog, send to social
- [ ] Note the campaign URL (with campaign ID)
- [ ] On Device 2 (or new browser):
  - [ ] Log in with same account
  - [ ] Paste the campaign URL
  - [ ] **Expected:** Blog content loads from backend
  - [ ] **Actual:** _____________

### Test 5.4: Refresh Persistence
- [ ] Generate blog, send to social
- [ ] On Social Manager page, refresh the page (F5)
- [ ] **Expected:** Blog content persists (fetched from backend)
- [ ] **Actual:** Content persisted? YES / NO

### Test 5.5: Expired Campaign
- [ ] Create a test campaign with expires_hours: 0 (requires API call)
- [ ] Try to load expired campaign
- [ ] **Expected:** HTTP 404 "Draft campaign has expired"
- [ ] **Actual:** _____________

---

## Backend Health Checks

### Database Table Creation
- [ ] Check Railway logs for "Draft campaigns table initialized"
- [ ] Verify no errors during table creation
- [ ] **Status:** _____________

### API Endpoints Available
Check that new endpoints are accessible:

```bash
# Health check
curl https://orla3-marketing-suite-app-production.up.railway.app/health

# Version check (should show draft-campaigns in tags)
curl https://orla3-marketing-suite-app-production.up.railway.app/docs
```
- [ ] Health endpoint returns 200
- [ ] API docs include draft-campaigns endpoints
- [ ] **Status:** _____________

---

## Error Scenarios to Test

### Test E1: Invalid Draft Campaign Data
```javascript
fetch('https://orla3-marketing-suite-app-production.up.railway.app/draft-campaigns', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  },
  body: JSON.stringify({
    campaign_type: "invalid",
    data: null  // Invalid
  })
}).then(r => console.log('Status:', r.status))
```
- [ ] **Expected:** HTTP 422 or 500 with error message
- [ ] **Actual:** _____________

### Test E2: Access Another User's Campaign
- [ ] Create campaign as User A
- [ ] Copy campaign ID
- [ ] Log in as User B
- [ ] Try to fetch User A's campaign
- [ ] **Expected:** HTTP 404 "not found or not owned by user"
- [ ] **Actual:** _____________

---

## Performance Checks

### Test P1: Response Times
Check that new endpoints don't slow down the system:

- [ ] Create draft campaign: < 500ms
- [ ] Fetch draft campaign: < 200ms
- [ ] Delete draft campaign: < 200ms
- [ ] **Actual times:** _____________ / _____________ / _____________

---

## Regression Testing

Ensure existing features still work:

- [ ] User registration works
- [ ] User login works
- [ ] Media library loads
- [ ] Content library loads
- [ ] Blog generation works (without sending to social)
- [ ] Social posting still works
- [ ] Calendar events work
- [ ] All existing pages load without errors

---

## Summary

**Total Tests:** 25
**Passed:** _____
**Failed:** _____
**Blocked:** _____

**Critical Issues Found:**
_____________________________________________________________
_____________________________________________________________

**Notes:**
_____________________________________________________________
_____________________________________________________________

**Tester Signature:** _______________  **Date:** _______________
