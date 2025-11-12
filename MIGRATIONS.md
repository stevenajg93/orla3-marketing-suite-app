# Database Migrations - ORLA³ Marketing Suite

## Migration Status Overview

This document tracks the status of all database migrations for the ORLA³ Marketing Suite PostgreSQL database.

---

## ✅ Applied Migrations (Production)

These migrations have been successfully applied to the production database:

### **002_add_stripe_fields.sql** ✅
- **Applied**: November 12, 2025
- **Purpose**: Add Stripe payment integration fields to users table
- **Changes**:
  - `stripe_customer_id` - Stripe customer reference
  - `subscription_status` - Current subscription state
  - `subscription_started_at` - Subscription start timestamp
  - `plan` - User subscription tier (free/starter/professional/business/enterprise)
- **Status**: **COMPLETE** - All Stripe payment features working

### **003_add_credit_tracking.sql** ✅
- **Applied**: November 12, 2025
- **Purpose**: Add credit-based usage system with complete audit trail
- **Changes**:
  - `credit_transactions` table - Complete credit audit trail
  - `credit_balance` column in users table
  - `monthly_credit_allocation` column
  - `total_credits_used`, `total_credits_purchased` columns
  - `last_credit_reset_at` column
  - PostgreSQL functions: `record_credit_transaction()`, `has_sufficient_credits()`, `reset_monthly_credits()`
- **Status**: **COMPLETE** - Credit system fully operational with enforcement

### **004_add_authentication.sql** ✅
- **Applied**: November 11, 2025
- **Purpose**: Add JWT authentication and multi-user support
- **Changes**:
  - `password_hash` (bcrypt) in users table
  - `email_verified`, `verification_token`, `verification_token_expires` columns
  - `reset_token`, `reset_token_expires` for password recovery
  - `role` column (system_admin/org_admin/user)
  - `is_locked`, `failed_login_attempts`, `locked_until` for security
  - `refresh_tokens` table for JWT token management
  - `audit_log` table for security tracking
  - Helper functions: `cleanup_expired_tokens()`, `record_login_attempt()`, `unlock_expired_locks()`
- **Status**: **COMPLETE** - Authentication fully functional with email verification

---

## ⚠️ Orphaned Migrations (Old/Superseded)

These migrations exist in the codebase but have been superseded or are no longer relevant:

### **001_add_generating_status.sql** ⚠️
- **Status**: **ORPHANED** - Superseded by newer migrations
- **Purpose**: Add generating status to content library
- **Action Required**: Can be safely deleted (functionality included in later migrations)

### **002_add_social_accounts.sql** ⚠️
- **Status**: **ORPHANED** - Superseded by authentication migration
- **Purpose**: Add social accounts tracking
- **Action Required**: Can be safely deleted (functionality included in 004_add_authentication.sql)

### **003_add_brand_assets.sql** ⚠️
- **Status**: **ORPHANED** - Brand assets already in schema.sql
- **Purpose**: Add brand_voice_assets table
- **Action Required**: Can be safely deleted (table already exists in schema.sql)

### **003_add_multi_tenant.sql** ⚠️
- **Status**: **DUPLICATE** - Duplicate of 001_add_multi_tenant_architecture.sql
- **Purpose**: Multi-tenant architecture migration (older version)
- **Action Required**: Delete this file, keep 001_add_multi_tenant_architecture.sql

---

## 🚧 Pending Migrations (Not Applied)

These migrations are prepared but have NOT been applied to production:

### **001_add_multi_tenant_architecture.sql** 🚧
- **Status**: **PENDING - BIG REFACTOR**
- **Purpose**: Full multi-tenant architecture with organization support
- **Size**: 12,824 bytes (large migration)
- **Changes**:
  - `organizations` table - Multi-organization support
  - `organization_users` table - User-organization mapping with roles
  - `user_cloud_storage_tokens` table - Per-user OAuth tokens (encrypted)
  - Add `organization_id` to all existing tables
  - System admin role for ORLA internal users
  - Enhanced audit logging
  - Data migration scripts for existing single-tenant data
- **Risk**: **HIGH** - Major schema changes, requires careful testing
- **Action Required**:
  - Review migration thoroughly
  - Test on staging/dev environment first
  - Backup production database before applying
  - May require application code updates
- **Documentation**: See `backend/MULTI_TENANT_ARCHITECTURE_PLAN.md`

---

## 📁 Loose SQL Files

### **backend/add_sample_content_column.sql**
- **Status**: **UNCLEAR** - Not in migrations/ directory
- **Purpose**: Unknown (needs investigation)
- **Action Required**: Review and either move to migrations/ or delete

---

## 🎯 Recommended Actions

### Immediate (Pre-Refactor Cleanup):
1. ✅ Create this MIGRATIONS.md file (tracking document)
2. 🗑️ Delete orphaned migrations:
   - `backend/migrations/001_add_generating_status.sql`
   - `backend/migrations/002_add_social_accounts.sql`
   - `backend/migrations/003_add_brand_assets.sql`
   - `backend/migrations/003_add_multi_tenant.sql` (keep 001_add_multi_tenant_architecture.sql)
3. 🔍 Investigate `backend/add_sample_content_column.sql`

### Future (Monster Refactor):
1. Rename applied migrations with `applied_` prefix:
   - `applied_002_add_stripe_fields.sql`
   - `applied_003_add_credit_tracking.sql`
   - `applied_004_add_authentication.sql`
2. Decide on multi-tenant architecture migration timing
3. Create proper migration tracking system (e.g., Alembic, Flyway)

---

## 📊 Current Database Schema

### Core Tables (Production):
- ✅ `users` - User accounts, authentication, subscriptions, credits
- ✅ `credit_transactions` - Credit audit trail
- ✅ `refresh_tokens` - JWT token management
- ✅ `audit_log` - Security event tracking
- ✅ `brand_strategy` - Per-user brand intelligence
- ✅ `brand_voice_assets` - Per-user uploaded materials
- ✅ `content_library` - Per-user generated content
- ✅ `competitors` - Per-user competitor tracking
- ✅ `competitor_analyses` - Competitor analysis results
- ✅ `calendar_events` - Per-user content calendar
- ✅ `published_posts` - Social media post tracking

### Schema File:
- `backend/schema.sql` - Base schema (applied manually, not tracked)

---

## 🔐 Migration Best Practices

1. **Always backup before migrations**: `pg_dump` before applying any migration
2. **Test on dev/staging first**: Never apply untested migrations to production
3. **Run migrations during low-traffic periods**: Minimize user impact
4. **Track applied migrations**: Update this document after each migration
5. **Use transactions**: Wrap migrations in BEGIN/COMMIT for rollback capability
6. **Version control**: All migrations tracked in git
7. **Document changes**: Update ORLA3_HANDOFF_PROMPT.md after major migrations

---

## 📞 Questions?

- For migration issues, check `backend/MULTI_TENANT_ARCHITECTURE_PLAN.md`
- For Stripe fields, see `STRIPE_SETUP_GUIDE.md`
- For general architecture, see `ORLA3_HANDOFF_PROMPT.md`

---

**Last Updated**: November 12, 2025
**Database Version**: 3.0 (Stripe + Credits + Authentication)
**Status**: ✅ Clean and ready for monster refactor
