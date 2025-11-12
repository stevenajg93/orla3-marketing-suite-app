# Stripe Payment Setup Guide for Orla³

## ✅ Already Completed
- Database migration applied (Stripe fields added to users table)
- Payment routes created (/payment/*)
- Payment gate added to login
- Email verification gate added

---

## 📋 Step 1: Create Products in Stripe Dashboard

Go to https://dashboard.stripe.com/products and create **7 products**:

### 1. Starter - Monthly
- **Name**: Orla³ Starter (Monthly)
- **Price**: £99.00 GBP
- **Billing**: Recurring - Monthly
- **Description**: 500 credits/month - Perfect for freelancers

### 2. Starter - Annual
- **Name**: Orla³ Starter (Annual)
- **Price**: £990.00 GBP
- **Billing**: Recurring - Yearly
- **Description**: 500 credits/month - Save 2 months with annual billing

### 3. Professional - Monthly
- **Name**: Orla³ Professional (Monthly)
- **Price**: £249.00 GBP
- **Billing**: Recurring - Monthly
- **Description**: 2,000 credits/month - Ideal for small businesses

### 4. Professional - Annual
- **Name**: Orla³ Professional (Annual)
- **Price**: £2,490.00 GBP
- **Billing**: Recurring - Yearly
- **Description**: 2,000 credits/month - Save 2 months with annual billing

### 5. Business - Monthly
- **Name**: Orla³ Business (Monthly)
- **Price**: £499.00 GBP
- **Billing**: Recurring - Monthly
- **Description**: 6,000 credits/month - For growing companies

### 6. Business - Annual
- **Name**: Orla³ Business (Annual)
- **Price**: £4,990.00 GBP
- **Billing**: Recurring - Yearly
- **Description**: 6,000 credits/month - Save 2 months with annual billing

### 7. Enterprise
- **Name**: Orla³ Enterprise
- **Price**: £999.00 GBP
- **Billing**: Recurring - Monthly
- **Description**: 20,000 credits/month - Custom solutions for large organizations

---

## 📋 Step 2: Copy Price IDs

After creating each product, Stripe will give you a **Price ID** (looks like `price_1ABC...`).

Copy each Price ID and add to Railway environment variables:

```bash
# Go to Railway → Your Project → Variables

# Starter
STRIPE_STARTER_MONTHLY_PRICE_ID=price_1ABC...
STRIPE_STARTER_ANNUAL_PRICE_ID=price_1DEF...

# Professional
STRIPE_PRO_MONTHLY_PRICE_ID=price_1GHI...
STRIPE_PRO_ANNUAL_PRICE_ID=price_1JKL...

# Business
STRIPE_BUSINESS_MONTHLY_PRICE_ID=price_1MNO...
STRIPE_BUSINESS_ANNUAL_PRICE_ID=price_1PQR...

# Enterprise
STRIPE_ENTERPRISE_PRICE_ID=price_1STU...
```

---

## 📋 Step 3: Configure Webhook

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. **Endpoint URL**: `https://your-railway-url.up.railway.app/payment/webhook`
4. **Events to listen for** - Select these 5 events:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.payment_failed`
5. Click "Add endpoint"
6. **Copy the Signing Secret** (starts with `whsec_...`)
7. Add to Railway:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

---

## 📋 Step 4: Verify Your Existing Stripe Keys

You mentioned Stripe keys are already in Railway. Verify these exist:

```bash
STRIPE_SECRET_KEY=sk_test_... (or sk_live_... for production)
STRIPE_PUBLISHABLE_KEY=pk_test_... (or pk_live_... for production)
```

**Important**: Make sure you're using **test keys** (`sk_test_` and `pk_test_`) during development!

---

## 📋 Step 5: Test the Payment Flow

1. Register a new test account on your platform
2. Verify email
3. Try to login → You should get: **"Please select and pay for a plan"**
4. Call `/payment/plans` endpoint to see available plans
5. Call `/payment/create-checkout` with a plan ID
6. You'll get a Stripe checkout URL
7. Use Stripe test card: `4242 4242 4242 4242` (any future expiry, any CVC)
8. Complete payment
9. Webhook fires → User's plan updated to paid
10. Login should now work!

---

## 🔧 Troubleshooting

**"Price ID not configured"**
- Make sure all 7 price IDs are added to Railway environment variables
- Restart Railway service after adding variables

**"Webhook signature verification failed"**
- Check `STRIPE_WEBHOOK_SECRET` is correct
- Make sure endpoint URL matches exactly

**"User still can't login after payment"**
- Check Railway logs for webhook processing
- Verify `subscription_status` column in database was updated to `'active'`
- Check user's `plan` field changed from `'free'` to the selected plan

---

## 📊 What Happens After Payment

1. User completes Stripe checkout
2. Stripe sends `checkout.session.completed` webhook to your backend
3. Backend updates user in database:
   ```sql
   UPDATE users SET
     plan = 'starter' | 'professional' | 'business' | 'enterprise',
     subscription_status = 'active',
     stripe_customer_id = 'cus_...',
     stripe_subscription_id = 'sub_...',
     subscription_started_at = NOW()
   WHERE id = user_id
   ```
4. User can now login and access the platform!

---

## 🚀 Ready for Production

When ready to go live:

1. Create the same 7 products in **Live Mode** on Stripe
2. Get **Live Price IDs**
3. Update Railway with **Live Keys**:
   ```bash
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   ```
4. Update webhook endpoint to production URL
5. Get **Live Webhook Secret**
6. Test with real card (but refund immediately!)

---

## ✅ Checklist

- [ ] Created 7 products in Stripe
- [ ] Copied all 7 Price IDs to Railway
- [ ] Configured webhook endpoint
- [ ] Added webhook secret to Railway
- [ ] Verified STRIPE_SECRET_KEY exists in Railway
- [ ] Verified STRIPE_PUBLISHABLE_KEY exists in Railway
- [ ] Tested payment flow end-to-end
- [ ] Confirmed users can't login without paying
- [ ] Confirmed users CAN login after paying

---

Need help? Check the Stripe docs:
- https://stripe.com/docs/billing/subscriptions/build-subscriptions
- https://stripe.com/docs/webhooks
