-- Migration 013: Pricing Tables
-- Move hardcoded pricing from payment.py to database
-- Date: November 20, 2025

-- Subscription plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_key VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'starter_monthly'
    name VARCHAR(100) NOT NULL,              -- e.g., 'Starter'
    price INTEGER NOT NULL,                  -- Price in pence (99 = £0.99)
    currency VARCHAR(3) DEFAULT 'GBP',
    interval VARCHAR(20) NOT NULL,           -- 'month' or 'year'
    credits INTEGER NOT NULL,                -- Monthly credit allocation
    stripe_price_id VARCHAR(255),            -- Stripe Price ID from env
    features JSONB DEFAULT '[]'::jsonb,      -- Array of feature strings
    is_active BOOLEAN DEFAULT true,          -- Can be purchased
    sort_order INTEGER DEFAULT 0,            -- Display order
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Credit packages table (one-time purchases)
CREATE TABLE IF NOT EXISTS credit_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_key VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'credits_500'
    name VARCHAR(100) NOT NULL,                 -- e.g., '500 Credits'
    price INTEGER NOT NULL,                     -- Price in pence
    currency VARCHAR(3) DEFAULT 'GBP',
    credits INTEGER NOT NULL,                   -- Credits granted
    stripe_price_id VARCHAR(255),               -- Stripe Price ID from env
    description TEXT,                           -- Short description
    badge VARCHAR(50),                          -- e.g., 'Best Value'
    price_per_credit NUMERIC(10, 4),            -- Calculated: price / credits
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Price change history (audit trail)
CREATE TABLE IF NOT EXISTS pricing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_type VARCHAR(50) NOT NULL,         -- 'subscription_plan' or 'credit_package'
    item_id UUID NOT NULL,                  -- References subscription_plans.id or credit_packages.id
    field_changed VARCHAR(100) NOT NULL,    -- e.g., 'price', 'credits', 'features'
    old_value TEXT,                         -- JSON-encoded old value
    new_value TEXT,                         -- JSON-encoded new value
    changed_by UUID REFERENCES users(id),   -- Admin who made the change
    changed_at TIMESTAMP DEFAULT NOW(),
    reason TEXT                             -- Optional: reason for change
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_subscription_plans_active ON subscription_plans(is_active, sort_order);
CREATE INDEX IF NOT EXISTS idx_credit_packages_active ON credit_packages(is_active, sort_order);
CREATE INDEX IF NOT EXISTS idx_pricing_history_item ON pricing_history(item_type, item_id, changed_at DESC);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_pricing_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER subscription_plans_updated
    BEFORE UPDATE ON subscription_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_pricing_timestamp();

CREATE TRIGGER credit_packages_updated
    BEFORE UPDATE ON credit_packages
    FOR EACH ROW
    EXECUTE FUNCTION update_pricing_timestamp();

-- Seed initial data from current hardcoded values

-- Subscription Plans (from payment.py lines 47-192)
INSERT INTO subscription_plans (plan_key, name, price, currency, interval, credits, stripe_price_id, features, sort_order) VALUES
('starter_monthly', 'Starter', 99, 'GBP', 'month', 500, '', to_jsonb(ARRAY[
    '500 credits/month',
    '~250 social captions or 100 blog posts',
    '25 AI-generated ultra images',
    '2 AI-generated videos (8-sec)',
    '1 brand voice profile',
    '9 social platform publishing',
    'Content calendar',
    'Basic competitor tracking',
    'Credit rollover (up to 250)'
]), 1),

('starter_annual', 'Starter (Annual)', 990, 'GBP', 'year', 500, '', to_jsonb(ARRAY[
    '500 credits/month',
    '2 months FREE (annual billing)',
    '~250 social captions or 100 blog posts',
    '25 AI-generated ultra images',
    '2 AI-generated videos (8-sec)',
    '1 brand voice profile',
    '9 social platform publishing',
    'Content calendar',
    'Basic competitor tracking',
    'Credit rollover (up to 250)'
]), 2),

('professional_monthly', 'Professional', 249, 'GBP', 'month', 2000, '', to_jsonb(ARRAY[
    '2,000 credits/month',
    '~1,000 social captions or 400 blog posts',
    '100 AI-generated ultra images',
    '10 AI-generated videos (8-sec)',
    '3 brand voice profiles',
    '9 social platform publishing',
    'Auto-publishing & scheduling',
    'Advanced competitor analysis (5 competitors)',
    'Priority support',
    'Credit rollover (up to 1,000)'
]), 3),

('professional_annual', 'Professional (Annual)', 2490, 'GBP', 'year', 2000, '', to_jsonb(ARRAY[
    '2,000 credits/month',
    '2 months FREE (annual billing)',
    '~1,000 social captions or 400 blog posts',
    '100 AI-generated ultra images',
    '10 AI-generated videos (8-sec)',
    '3 brand voice profiles',
    '9 social platform publishing',
    'Auto-publishing & scheduling',
    'Advanced competitor analysis (5 competitors)',
    'Priority support',
    'Credit rollover (up to 1,000)'
]), 4),

('business_monthly', 'Business', 499, 'GBP', 'month', 6000, '', to_jsonb(ARRAY[
    '6,000 credits/month',
    '~3,000 social captions or 1,200 blog posts',
    '300 AI-generated ultra images',
    '30 AI-generated videos (8-sec)',
    '10 brand voice profiles',
    '9 social platform publishing',
    'Multi-user collaboration (5 seats)',
    'Unlimited competitor tracking',
    'API access',
    'White-label options',
    'Credit rollover (up to 3,000)'
]), 5),

('business_annual', 'Business (Annual)', 4990, 'GBP', 'year', 6000, '', to_jsonb(ARRAY[
    '6,000 credits/month',
    '2 months FREE (annual billing)',
    '~3,000 social captions or 1,200 blog posts',
    '300 AI-generated ultra images',
    '30 AI-generated videos (8-sec)',
    '10 brand voice profiles',
    '9 social platform publishing',
    'Multi-user collaboration (5 seats)',
    'Unlimited competitor tracking',
    'API access',
    'White-label options',
    'Credit rollover (up to 3,000)'
]), 6),

('enterprise', 'Enterprise', 999, 'GBP', 'month', 20000, '', to_jsonb(ARRAY[
    '20,000 credits/month',
    '~10,000 social captions or 4,000 blog posts',
    '1,000 AI-generated ultra images',
    '100 AI-generated videos (8-sec)',
    'Unlimited brand voices',
    '9 social platform publishing',
    'Unlimited team members',
    'Dedicated account manager',
    'Custom integrations',
    'SLA guarantees',
    'Full credit rollover (unlimited)'
]), 7);

-- Credit Packages (from payment.py lines 195-233)
INSERT INTO credit_packages (package_key, name, price, currency, credits, stripe_price_id, description, badge, price_per_credit, sort_order) VALUES
('credits_500', '500 Credits', 125, 'GBP', 500, '', 'Emergency credit top-up', NULL, 0.25, 1),
('credits_1000', '1,000 Credits', 200, 'GBP', 1000, '', 'Credit boost for campaigns', NULL, 0.20, 2),
('credits_2500', '2,500 Credits', 400, 'GBP', 2500, '', 'Big campaign pack', 'Best Value', 0.16, 3),
('credits_5000', '5,000 Credits', 650, 'GBP', 5000, '', 'Major campaign pack', NULL, 0.13, 4);

-- Grant pricing management permissions to super admins
COMMENT ON TABLE subscription_plans IS 'Database-driven subscription pricing (replaces hardcoded PRICING_PLANS in payment.py)';
COMMENT ON TABLE credit_packages IS 'Database-driven credit packages (replaces hardcoded CREDIT_PACKAGES in payment.py)';
COMMENT ON TABLE pricing_history IS 'Audit trail for all pricing changes';
