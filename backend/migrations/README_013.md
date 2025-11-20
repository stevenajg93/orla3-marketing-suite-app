# Migration 013: Database-Driven Pricing

**Date:** November 20, 2025
**Type:** Schema + Data
**Complexity:** Medium
**Estimated Time:** 5-10 minutes

## Overview

Moves all pricing from hardcoded Python dictionaries to PostgreSQL database tables. This allows super admins to update pricing without code deployments.

## What Changed

### Before
- Pricing hardcoded in `backend/routes/payment.py` (lines 47-233)
- Changing prices required code changes + deployment
- No audit trail for price changes

### After
- All pricing stored in `subscription_plans` and `credit_packages` tables
- Admin API endpoints for pricing management
- Full audit trail in `pricing_history` table
- Zero-downtime price updates

## Files Changed

1. `backend/migrations/013_pricing_tables.sql` - NEW - Database migration
2. `backend/routes/payment.py` - Refactored to fetch from database
3. `backend/routes/admin_pricing.py` - NEW - Admin pricing management API
4. `backend/main.py` - Registered admin_pricing router

## How to Apply Migration

### Option 1: Railway Dashboard (Recommended for Production)

1. Go to Railway dashboard: https://railway.com/project/b5320646-39a5-4267-a1d0-65d72f0f580d
2. Click on PostgreSQL service
3. Click "Query" tab
4. Copy and paste contents of `013_pricing_tables.sql`
5. Click "Run Query"
6. Verify tables created:
   ```sql
   SELECT COUNT(*) FROM subscription_plans;  -- Should return 7
   SELECT COUNT(*) FROM credit_packages;     -- Should return 4
   ```

### Option 2: psql Command Line

```bash
# Using Railway DATABASE_URL
psql $DATABASE_URL -f backend/migrations/013_pricing_tables.sql

# Verify
psql $DATABASE_URL -c "SELECT plan_key, name, price FROM subscription_plans;"
```

### Option 3: Python Script

```bash
cd backend
python3 << 'EOF'
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

with open('migrations/013_pricing_tables.sql', 'r') as f:
    sql = f.read()
    cur.execute(sql)
    conn.commit()

print("✅ Migration 013 applied successfully")
cur.close()
conn.close()
EOF
```

## Verification Steps

After applying the migration:

1. **Check Tables Exist:**
   ```sql
   \dt subscription_plans
   \dt credit_packages
   \dt pricing_history
   ```

2. **Check Data Seeded:**
   ```sql
   SELECT COUNT(*) FROM subscription_plans;  -- Expected: 7
   SELECT COUNT(*) FROM credit_packages;     -- Expected: 4
   ```

3. **Test API Endpoints:**
   ```bash
   # Get plans (should return database data)
   curl https://orla3-marketing-suite-app-production.up.railway.app/payment/plans

   # Get packages (should return database data)
   curl https://orla3-marketing-suite-app-production.up.railway.app/payment/credit-packages
   ```

4. **Test Admin Endpoints (requires super admin):**
   ```bash
   # Get all plans including inactive
   curl -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
     https://orla3-marketing-suite-app-production.up.railway.app/admin/pricing/plans
   ```

## New Admin API Endpoints

All endpoints require super admin authentication.

### Subscription Plans
- `GET /admin/pricing/plans` - Get all plans (including inactive)
- `GET /admin/pricing/plans/{plan_key}` - Get single plan
- `PATCH /admin/pricing/plans/{plan_key}` - Update plan

### Credit Packages
- `GET /admin/pricing/packages` - Get all packages (including inactive)
- `GET /admin/pricing/packages/{package_key}` - Get single package
- `PATCH /admin/pricing/packages/{package_key}` - Update package

### History
- `GET /admin/pricing/history?limit=50` - Get price change history

## Example: Update Pricing

```bash
# Update Starter plan price from £0.99 to £1.49
curl -X PATCH \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"price": 149}' \
  https://orla3-marketing-suite-app-production.up.railway.app/admin/pricing/plans/starter_monthly

# Result: Price updated immediately, no deployment needed
# History logged in pricing_history table
```

## Rollback Plan

If issues occur, rollback is simple:

```sql
-- Drop new tables
DROP TABLE IF EXISTS pricing_history CASCADE;
DROP TABLE IF EXISTS credit_packages CASCADE;
DROP TABLE IF EXISTS subscription_plans CASCADE;

-- Backend will fail gracefully with 500 error on pricing endpoints
-- Old hardcoded values are in git history (commit before this migration)
```

Then revert backend code changes:
```bash
git checkout HEAD~1 backend/routes/payment.py backend/routes/admin_pricing.py backend/main.py
```

## Testing Checklist

- [ ] Migration applied without errors
- [ ] 7 subscription plans seeded
- [ ] 4 credit packages seeded
- [ ] GET /payment/plans returns correct data
- [ ] GET /payment/credit-packages returns correct data
- [ ] Existing payment flows still work (create checkout)
- [ ] Admin endpoints accessible to super admins
- [ ] Admin endpoints blocked for non-super-admins
- [ ] Price updates persist after backend restart

## Performance Impact

- **Minimal:** Pricing queries are fast (indexed, small tables)
- **Caching:** Consider adding Redis caching in future if needed
- **Database Load:** +3 queries per checkout (vs 0 before)

## Future Enhancements

1. **Admin UI:** Add pricing management to `/admin` portal
2. **Caching:** Cache pricing in Redis (15min TTL)
3. **A/B Testing:** Store multiple price points for experiments
4. **Regional Pricing:** Add country-specific pricing
5. **Discounts:** Promotional pricing and coupon codes

## Questions or Issues?

Contact: s.gillespie@gecslabs.com
