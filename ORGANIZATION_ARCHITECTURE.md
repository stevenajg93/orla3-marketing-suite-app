# Organization Multi-Tenant Architecture

## Overview

ORLA³ supports **team collaboration** through organizations. Each organization has a subscription tier that determines the number of users allowed.

---

## User Limits Per Tier

| Tier | Monthly Price | Included Users | Additional Users | Max Users |
|------|---------------|----------------|------------------|-----------|
| **Starter** | $99 | 1 | Not available | 1 |
| **Professional** | $249 | 3 | $50/user/mo | 10 |
| **Business** | $499 | 10 | $35/user/mo | 50 |
| **Enterprise** | $999+ | 25 | Custom pricing | Unlimited |

---

## Database Schema

### **Organizations Table**

Each organization represents a company/team workspace.

```sql
organizations (
    id UUID PRIMARY KEY,
    name TEXT,                    -- "Acme Marketing Inc."
    slug TEXT UNIQUE,             -- "acme-marketing-inc"
    subscription_tier TEXT,       -- starter|professional|business|enterprise
    max_users INTEGER,            -- Based on tier + add-ons
    current_user_count INTEGER,   -- Enforced by trigger
    shared_drive_id TEXT,         -- Google Shared Drive ID
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT
)
```

### **Organization Members (Junction Table)**

```sql
organization_members (
    id UUID PRIMARY KEY,
    organization_id UUID,
    user_id UUID,
    role user_role,              -- owner|admin|member|viewer
    is_active BOOLEAN,
    invited_at TIMESTAMPTZ,
    joined_at TIMESTAMPTZ
)
```

### **User Roles & Permissions**

| Role | Can Invite Users | Can Manage Billing | Can Connect Services | Can Publish Content | Can View Analytics |
|------|------------------|--------------------|--------------------|---------------------|-------------------|
| **Owner** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Admin** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Member** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Viewer** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Cloud Storage Integration

### **Personal Storage (Deprecated)**
- ❌ Personal Google Drive, OneDrive, Dropbox no longer supported
- Users' personal files are never accessed for security/privacy

### **Organization-Level Storage Options**

#### **Option 1: Google Shared Drives** (Recommended for Google Workspace)
- ✅ Connect a Google Shared Drive to your organization
- Only **owners/admins** can connect
- All team members access the same shared drive
- Requires: Google Workspace Business or higher

#### **Option 2: OneDrive for Business / SharePoint** (Recommended for Microsoft 365)
- ✅ Connect SharePoint document library or OneDrive Business shared folder
- Team-wide access via SharePoint permissions
- Requires: Microsoft 365 Business Standard or higher

#### **Option 3: Dropbox Business Team Folders** (Recommended for Dropbox Business)
- ✅ Connect Dropbox Business Team Folder
- Shared across entire team
- Requires: Dropbox Business or higher

#### **Option 4: ORLA³ Native Storage** (Fallback - No shared drive required)
- ✅ Upload files directly to ORLA³
- Stored in secure Google Cloud Storage bucket
- Organization-owned, accessible to all team members
- **5GB included** in Professional, **25GB** in Business, **100GB** in Enterprise
- Accessible from Media Library like any other cloud storage

**Benefits of Organization-Level Storage:**
- Files persist when users leave the organization
- Centralized brand asset management
- Proper access control and team collaboration
- No personal file mixing with company assets

---

## Migration Strategy

### **Phase 1: Database Migration (Week 1)**

1. Run `migrations/011_add_organizations_and_teams.sql`
2. Automatically creates "Personal Workspace" organization for each existing user
3. Sets user as "owner" of their personal organization
4. Migrates all existing content/connections to their organization

### **Phase 2: Organization Cloud Storage Selection (Week 1-2)**

**Frontend Changes:**
- `/dashboard/settings/cloud-storage` - Redesign for organization storage
- Show 4 options: Google Shared Drive, OneDrive SharePoint, Dropbox Team, ORLA³ Native
- List available shared resources from each provider's API
- Display current storage usage for orla3_native
- Upload interface for orla3_native storage

**Backend Changes:**
- Update `cloud_storage_oauth.py` to list shared/team drives for all providers:
  - Google: List shared drives via Drive API
  - OneDrive: List SharePoint sites via Graph API
  - Dropbox: List team folders via Dropbox API
- Store `storage_provider` and `storage_drive_id` in `organizations` table
- Update `cloud_storage_browse.py` to query organization storage only
- Add upload endpoint for orla3_native storage (saves to GCS bucket)

**API Endpoints:**
```
GET  /cloud-storage/organization/google-shared-drives      # List available Google Shared Drives
GET  /cloud-storage/organization/onedrive-sharepoint       # List SharePoint sites/libraries
GET  /cloud-storage/organization/dropbox-teams             # List Dropbox team folders
POST /cloud-storage/organization/connect                   # Connect org to storage provider
GET  /cloud-storage/organization/browse                    # Browse org's connected storage
POST /cloud-storage/organization/upload                    # Upload to orla3_native (GCS)
DELETE /cloud-storage/organization/file/{id}               # Delete from orla3_native
```

**Storage Quotas (orla3_native only):**
- Starter: Not available (must use shared drive)
- Professional: 5GB included
- Business: 25GB included
- Enterprise: 100GB included

### **Phase 3: Landing Page Updates (Week 2)**

Update `/app/page.tsx` with team pricing:

**Starter Plan:**
- "Perfect for solo creators and freelancers"
- "1 user included"

**Professional Plan:**
- "Ideal for small teams and agencies"
- "3 users included"
- "Additional users: $50/user/month"

**Business Plan:**
- "For growing marketing teams"
- "10 users included"
- "Additional users: $35/user/month"

**Enterprise Plan:**
- "Custom solutions for large organizations"
- "25+ users included"
- "Unlimited team members available"
- "Contact sales for pricing"

### **Phase 4: Team Management UI (Week 3)**

New page: `/dashboard/team`

**Features:**
- List all organization members
- Invite new members (if under user limit)
- Change member roles
- Deactivate members
- View user activity logs

**Permissions:**
- Only owners/admins can access
- Starter plan users don't see this page (single user)

### **Phase 5: Billing Updates (Week 4)**

**Stripe Integration:**
- Add "Team Member" add-on product in Stripe
- Update checkout flow to include user count selection
- Create webhook for seat changes
- Handle proration when adding/removing users

---

## User Workflows

### **New Organization Sign-up**

1. User registers → Creates account
2. System creates "Personal Workspace" organization (tier: starter, users: 1)
3. User is set as "owner"
4. User sees onboarding flow
5. User upgrades to Professional+ → Can invite team members

### **Inviting Team Members**

1. Owner/Admin goes to `/dashboard/team`
2. Clicks "Invite Member"
3. Enters email + role (admin|member|viewer)
4. System checks: `current_user_count < max_users`
5. If allowed: Sends email invitation
6. New user accepts invite → Joins organization
7. `current_user_count` increments (via database trigger)

### **Connecting Shared Drive**

1. Owner/Admin goes to `/dashboard/settings/cloud-storage`
2. Clicks "Connect Google Drive"
3. OAuth flow → User authorizes Google Workspace
4. System calls Google Drive API: `GET /drives` (lists shared drives)
5. User selects shared drive from dropdown
6. System stores `shared_drive_id` in organizations table
7. All team members now access this shared drive in Media Library

### **Switching Organizations (Future)**

Users can be members of multiple organizations:

1. User clicks organization switcher in navbar
2. Selects different organization
3. `current_organization_id` updates in users table
4. All queries now filter by new organization
5. User sees that organization's content/settings

---

## Security Considerations

### **Data Isolation**

All queries must filter by `organization_id`:

```sql
-- WRONG: Shows all content across all orgs
SELECT * FROM content_library WHERE user_id = $1;

-- CORRECT: Shows only current org's content
SELECT * FROM content_library
WHERE organization_id = $2 AND user_id = $1;
```

### **Permission Checks**

Before any admin action:

```sql
SELECT user_has_org_permission(
    $user_id,
    $organization_id,
    'admin'::user_role
);
```

### **Stripe Subscription Mapping**

- Each organization has ONE Stripe subscription
- Owner's Stripe customer ID is used for billing
- Changing subscription tier updates `max_users` limit
- Database constraint prevents exceeding limit

---

## Admin Panel Requirements

### **Organization Dashboard** (`/dashboard/organization`)

**Metrics:**
- Current users / Max users
- Subscription tier & next billing date
- Total credits used this month
- Active social connections

**Quick Actions:**
- Invite team member
- Upgrade plan
- Connect shared drive
- View billing

### **Team Management** (`/dashboard/team`)

**Member List:**
- Avatar, Name, Email, Role, Last Active
- Actions: Edit Role, Deactivate, Remove

**Invite Flow:**
- Email input with role selector
- Preview of invitation email
- "Invite" button (disabled if at user limit)

**User Limit Warning:**
- "You've used 9/10 seats. Upgrade to add more users."
- Link to upgrade plan

---

## Implementation Checklist

### **Backend** (Phase 1: COMPLETED ✅)

- [x] Run migration 011 ✅ **DONE** (Nov 16, 2025)
- [x] Add organization context to middleware ✅ **DONE** (`get_user_context()` in `auth_dependency.py`)
- [x] Update all queries to filter by organization_id ✅ **DONE** (Cloud storage routes updated)
- [ ] Add Google Shared Drive API endpoints ⏳ **IN PROGRESS**
- [ ] Create team invitation email templates
- [ ] Add Stripe webhook for seat changes
- [x] Add permission checking functions ✅ **DONE** (`user_has_org_permission()` in migration 011)

### **Frontend** (Phase 2: PENDING)

- [ ] Update landing page with team pricing
- [ ] Create `/dashboard/team` page
- [ ] Add shared drive selector to cloud storage settings
- [ ] Add organization switcher to navbar
- [ ] Add user limit warnings
- [ ] Update checkout flow for team sizes
- [ ] Create `/admin` super admin dashboard **NEW**

### **Database** (Phase 1: COMPLETED ✅)

- [x] Back up production database ✅ **DONE**
- [x] Test migration on staging ✅ **DONE** (Tested locally)
- [x] Run migration on production ✅ **DONE** (Nov 16, 2025 - 5 organizations created)
- [x] Verify all existing users have organizations ✅ **DONE** (All 5 users migrated)
- [x] Monitor for constraint violations ✅ **DONE** (Fixed `selected_folders`, `created_at` column issues)

### **Super Admin** (Phase 3: IN PROGRESS)

- [ ] Add `is_super_admin` column to users table
- [ ] Add `credits_exempt` column to users table
- [ ] Set s.gillespie@gecslabs.com as super admin
- [ ] Create admin API routes (`/admin/*`)
- [ ] Build admin dashboard UI (`/admin`)
- [ ] Platform statistics and user management

---

## Rollout Plan

### **Week 1: Database + Backend**
- Run migration 011 on production (off-hours)
- Deploy backend changes with organization filtering
- Add shared drive API endpoints
- Monitor logs for any issues

### **Week 2: Frontend Team Features**
- Deploy team management UI
- Update landing page
- Add invite flow
- Test with pilot customers

### **Week 3: Google Drive Migration**
- Add shared drive selector
- Migrate existing Drive connections
- Email customers about shared drive requirement
- Provide migration guide

### **Week 4: Billing Integration**
- Deploy Stripe team pricing
- Add seat management
- Test upgrade/downgrade flows
- Launch publicly

---

## Success Metrics

- **Adoption**: % of Professional+ customers who invite team members
- **Upgrades**: % of Starter users who upgrade for team features
- **Shared Drive**: % of organizations using shared drives vs personal drives
- **Retention**: Team account retention vs single-user retention

**Target:** 60% of Professional+ customers invite at least 1 team member within 30 days.
