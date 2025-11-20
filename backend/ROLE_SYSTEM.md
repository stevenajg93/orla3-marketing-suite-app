# ORLA³ Role System Documentation

**Last Updated:** November 20, 2025
**Version:** 2.0 (Unified System)

---

## Overview

ORLA³ uses **TWO DISTINCT ROLE CONCEPTS** that serve different purposes:

1. **Organization Roles** = Permission levels (authorization)
2. **Job Functions** = What people do (workflow assignment)

**These are NOT interchangeable.** This document clarifies the distinction.

---

## 1. Organization Roles (Permission System)

**Purpose:** Control what users CAN and CANNOT do in the system (authorization).

**Location:**
- Database: `organization_members.role` column
- Code: `backend/routes/organization.py`
- Models: `org_role` field in collaboration models

### Role Hierarchy

```
owner > admin > member > viewer
```

### Permissions Matrix

| Action | owner | admin | member | viewer |
|--------|-------|-------|--------|--------|
| Manage billing | ✅ | ❌ | ❌ | ❌ |
| Invite users | ✅ | ✅ | ❌ | ❌ |
| Connect services | ✅ | ✅ | ❌ | ❌ |
| Create content | ✅ | ✅ | ✅ | ❌ |
| Edit content | ✅ | ✅ | ✅ | ❌ |
| Publish content | ✅ | ✅ | ❌ | ❌ |
| View analytics | ✅ | ✅ | ✅ | ✅ |

### When to Use

- **Authorization checks** (can user perform this action?)
- **UI permission gates** (should we show this button?)
- **API endpoint validation** (is user allowed to call this?)

---

## 2. Job Functions (Workflow System)

**Purpose:** Describe what users DO for task assignment (workflow optimization).

**Location:**
- Code: `backend/routes/collaboration.py`
- Models: `job_function` field (optional)
- AI prompts: Used for intelligent task assignment

### Available Job Functions

| Function | Description | Typical Tasks |
|----------|-------------|---------------|
| `editor` | Writes and edits text content | Write blog posts, edit copy, proofread |
| `designer` | Creates visual content | Design graphics, edit videos, create templates |
| `content_creator` | Creates original media | Film videos, take photos, record audio |
| `reviewer` | Reviews for quality/compliance | Quality check, brand compliance, legal review |
| `approver` | Final approval before publishing | Sign-off, final approval, go-live decision |

### When to Use

- **AI workflow suggestions** (who should do this task?)
- **Task assignment** (match work to expertise)
- **Team optimization** (balance workload by function)

### Important Notes

- Job function is **OPTIONAL** (can be null)
- Job function does **NOT** grant permissions
- A "designer" with `viewer` org_role still cannot edit content
- A "member" can have `approver` job function but cannot actually publish

---

## 3. How They Work Together

### Example Users

```json
{
  "users": [
    {
      "id": "user-1",
      "name": "Sarah",
      "org_role": "admin",
      "job_function": "editor"
    },
    {
      "id": "user-2",
      "name": "Mike",
      "org_role": "member",
      "job_function": "designer"
    },
    {
      "id": "user-3",
      "name": "Client Contact",
      "org_role": "viewer",
      "job_function": null
    }
  ]
}
```

### Assignment Logic

**Task:** "Create a blog post graphic"

1. **AI considers job_function:** Mike is a designer ✅
2. **System validates org_role:** Mike is a member (can create) ✅
3. **Assignment made:** Mike gets the task ✅

**Task:** "Publish the blog post"

1. **AI might suggest:** Sarah (has approver function)
2. **System validates org_role:** Sarah is admin (can publish) ✅
3. **Assignment made:** Sarah gets the task ✅

**Task:** "Approve final video"

1. **AI might suggest:** Mike (designer who created it)
2. **System validates org_role:** Mike is member (CANNOT publish) ❌
3. **Assignment filtered:** Task NOT assigned to Mike
4. **System suggests:** Notify admins/owners instead

---

## 4. Code Implementation

### In Collaboration Endpoint (`collaboration.py`)

```python
class User(BaseModel):
    id: str
    name: str
    email: str
    org_role: Literal["owner", "admin", "member", "viewer"]  # Permission level
    job_function: Optional[Literal["editor", "designer", "content_creator", "reviewer", "approver"]] = None  # What they do

def validate_user_can_perform_action(org_role: str, next_action: str) -> bool:
    """Validates org_role permits the action."""
    if org_role in ["owner", "admin"]:
        return True  # Can do everything
    elif org_role == "member":
        return not requires_publish(next_action)  # Cannot publish
    else:  # viewer
        return False  # Cannot be assigned work
```

### Validation Flow

1. AI generates workflow suggestions
2. System validates each assignment:
   - Check user exists in organization ✅
   - Check org_role permits the action ✅
   - Filter invalid assignments ✅
3. Return validated assignments + notification if any filtered

---

## 5. Frontend Integration

### When Calling Collaboration API

```typescript
// ✅ CORRECT: Include both role types
const users = teamMembers.map(member => ({
  id: member.id,
  name: member.name,
  email: member.email,
  org_role: member.organizationRole,  // From org membership
  job_function: member.jobFunction    // From user profile (optional)
}));

await api.post('/collab/workflow', {
  users,
  content_items: items,
  action: 'assign_workflow'
});
```

```typescript
// ❌ WRONG: Only passing one role type
const users = teamMembers.map(member => ({
  id: member.id,
  name: member.name,
  email: member.email,
  role: member.role  // Which role? Unclear!
}));
```

### Displaying User Information

```typescript
// Show both when relevant
<UserCard>
  <Name>{user.name}</Name>
  <Badge>{user.org_role}</Badge>  {/* Permission level */}
  {user.job_function && (
    <Tag>{user.job_function}</Tag>  {/* What they do */}
  )}
</UserCard>
```

---

## 6. Migration Guide

### For Existing Code

**Old collaboration API (broken):**
```python
class User(BaseModel):
    role: Literal["admin", "editor", "designer", "client", "viewer"]  # Ambiguous!
```

**New collaboration API (fixed):**
```python
class User(BaseModel):
    org_role: Literal["owner", "admin", "member", "viewer"]  # Permission
    job_function: Optional[Literal["editor", "designer", ...]]  # What they do
```

### Update Frontend Calls

1. Find all calls to `/collab/workflow`
2. Update user objects to include both `org_role` and `job_function`
3. Test that assignments respect permissions

### Update Database Schema (if needed)

```sql
-- If storing job functions in database:
ALTER TABLE users ADD COLUMN job_function TEXT CHECK (
  job_function IN ('editor', 'designer', 'content_creator', 'reviewer', 'approver')
);

-- Keep organization_members.role as is (this is org_role)
```

---

## 7. Common Pitfalls

### ❌ DON'T: Confuse the Two Systems

```python
# WRONG: Using job_function for authorization
if user.job_function == "approver":
    allow_publish()  # ❌ Job function doesn't grant permissions!

# CORRECT: Use org_role for authorization
if user.org_role in ["owner", "admin"]:
    allow_publish()  # ✅ Only org_role grants permissions
```

### ❌ DON'T: Grant Permissions Based on Job Function

```python
# WRONG
if user.job_function == "editor":
    allow_edit_content()  # ❌ A viewer with editor function cannot edit!

# CORRECT
if user.org_role in ["owner", "admin", "member"]:
    allow_edit_content()  # ✅ Check org_role first
```

### ✅ DO: Use Job Function for AI Suggestions Only

```python
# CORRECT: Use job_function to match work to expertise
def suggest_assignee(task, users):
    # 1. Filter by permission
    eligible = [u for u in users if can_perform(u.org_role, task)]

    # 2. Match by job function
    best_match = next(
        u for u in eligible
        if u.job_function == task.required_function
    )

    return best_match
```

---

## 8. Summary

| Aspect | Organization Roles | Job Functions |
|--------|-------------------|---------------|
| **Purpose** | Authorization | Workflow optimization |
| **Required?** | Yes (always) | No (optional) |
| **Grants permissions?** | Yes ✅ | No ❌ |
| **Used for?** | Access control | Task assignment |
| **Enforced by?** | Database + API | AI + validation |
| **Field name** | `org_role` | `job_function` |

**Golden Rule:**
- Use `org_role` to decide IF someone can do something
- Use `job_function` to decide WHO should do it (among those who can)

---

**Questions?** Refer to:
- `backend/routes/organization.py` - Organization permission system
- `backend/routes/collaboration.py` - Workflow assignment system
- `ORGANIZATION_ARCHITECTURE.md` - Organization structure docs
