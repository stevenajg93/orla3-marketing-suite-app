-- ============================================================================
-- Migration: Add Credit Tracking System
-- Purpose: Track user credit balance, usage, and transactions
-- ============================================================================

-- Add credit columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS credit_balance INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_credit_allocation INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_credit_reset_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_credits_purchased INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_credits_used INTEGER DEFAULT 0;

-- Create credit transactions table for audit trail
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL, -- 'earned', 'spent', 'purchased', 'refund', 'reset'
    amount INTEGER NOT NULL, -- positive for credits added, negative for credits spent
    balance_after INTEGER NOT NULL, -- credit balance after this transaction

    -- What was the credit used for?
    operation_type VARCHAR(100), -- 'social_caption', 'blog_post', 'ai_image_standard', 'ai_image_ultra', 'ai_video'
    operation_details JSONB, -- Additional context (e.g., platform, content type, etc.)

    -- Reference to payment/purchase
    stripe_payment_intent_id VARCHAR(255),
    stripe_charge_id VARCHAR(255),

    -- Metadata
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for credit_transactions table
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created ON credit_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_operation ON credit_transactions(operation_type);

-- Create function to record credit transaction
CREATE OR REPLACE FUNCTION record_credit_transaction(
    p_user_id UUID,
    p_transaction_type VARCHAR,
    p_amount INTEGER,
    p_operation_type VARCHAR DEFAULT NULL,
    p_operation_details JSONB DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_new_balance INTEGER;
    v_transaction_id UUID;
BEGIN
    -- Get current balance and update it
    SELECT credit_balance INTO v_new_balance
    FROM users
    WHERE id = p_user_id;

    -- Calculate new balance
    v_new_balance := v_new_balance + p_amount;

    -- Prevent negative balance
    IF v_new_balance < 0 THEN
        RAISE EXCEPTION 'Insufficient credits. Current balance: %, Requested: %', v_new_balance - p_amount, ABS(p_amount);
    END IF;

    -- Update user balance
    UPDATE users
    SET credit_balance = v_new_balance,
        total_credits_used = total_credits_used + CASE WHEN p_amount < 0 THEN ABS(p_amount) ELSE 0 END,
        total_credits_purchased = total_credits_purchased + CASE WHEN p_transaction_type = 'purchased' THEN p_amount ELSE 0 END
    WHERE id = p_user_id;

    -- Insert transaction record
    INSERT INTO credit_transactions (
        user_id, transaction_type, amount, balance_after,
        operation_type, operation_details, description
    ) VALUES (
        p_user_id, p_transaction_type, p_amount, v_new_balance,
        p_operation_type, p_operation_details, p_description
    ) RETURNING id INTO v_transaction_id;

    RETURN v_transaction_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to check if user has enough credits
CREATE OR REPLACE FUNCTION has_sufficient_credits(
    p_user_id UUID,
    p_required_credits INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    v_balance INTEGER;
BEGIN
    SELECT credit_balance INTO v_balance
    FROM users
    WHERE id = p_user_id;

    RETURN v_balance >= p_required_credits;
END;
$$ LANGUAGE plpgsql;

-- Create function to reset monthly credits
CREATE OR REPLACE FUNCTION reset_monthly_credits(
    p_user_id UUID
) RETURNS VOID AS $$
DECLARE
    v_monthly_allocation INTEGER;
    v_current_balance INTEGER;
    v_rollover_limit INTEGER;
    v_new_balance INTEGER;
    v_plan VARCHAR;
BEGIN
    -- Get user's plan and allocation
    SELECT monthly_credit_allocation, credit_balance, plan
    INTO v_monthly_allocation, v_current_balance, v_plan
    FROM users
    WHERE id = p_user_id;

    -- Calculate rollover limit based on plan
    v_rollover_limit := CASE v_plan
        WHEN 'starter' THEN 250
        WHEN 'professional' THEN 1000
        WHEN 'business' THEN 3000
        WHEN 'enterprise' THEN 999999 -- unlimited
        ELSE 0
    END;

    -- Calculate new balance with rollover
    v_new_balance := LEAST(v_current_balance, v_rollover_limit) + v_monthly_allocation;

    -- Update user
    UPDATE users
    SET credit_balance = v_new_balance,
        last_credit_reset_at = NOW()
    WHERE id = p_user_id;

    -- Record transaction
    PERFORM record_credit_transaction(
        p_user_id,
        'reset',
        v_monthly_allocation,
        NULL,
        jsonb_build_object('rollover', LEAST(v_current_balance, v_rollover_limit)),
        'Monthly credit reset'
    );
END;
$$ LANGUAGE plpgsql;

-- Initialize credit balances for existing users based on their plans
UPDATE users
SET monthly_credit_allocation = CASE plan
    WHEN 'starter' THEN 500
    WHEN 'professional' THEN 2000
    WHEN 'business' THEN 6000
    WHEN 'enterprise' THEN 20000
    ELSE 0
END,
credit_balance = CASE plan
    WHEN 'starter' THEN 500
    WHEN 'professional' THEN 2000
    WHEN 'business' THEN 6000
    WHEN 'enterprise' THEN 20000
    ELSE 0
END,
last_credit_reset_at = NOW()
WHERE monthly_credit_allocation = 0;

-- Create initial transaction records for existing users
INSERT INTO credit_transactions (user_id, transaction_type, amount, balance_after, description)
SELECT id, 'earned', credit_balance, credit_balance, 'Initial credit allocation'
FROM users
WHERE credit_balance > 0;
