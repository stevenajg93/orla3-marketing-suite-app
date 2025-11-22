"""
Stripe Payment Integration
Handles subscription creation, webhooks, and payment status
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
import stripe
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from utils.auth import decode_token
from utils.credits import add_credits
from db_pool import get_db_connection  # Use connection pool

router = APIRouter()
logger = setup_logger(__name__)

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def get_user_from_token(request: Request):
    """Extract user_id from JWT token"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get('sub')  # user_id

# ===================================================================
# DATABASE-DRIVEN PRICING
# Pricing now stored in subscription_plans and credit_packages tables
# Migration: 013_pricing_tables.sql
# ===================================================================

def get_pricing_plans_from_db():
    """Fetch subscription plans from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT plan_key, name, price, currency, interval, credits,
                       stripe_price_id, features, is_active
                FROM subscription_plans
                WHERE is_active = true
                ORDER BY sort_order
            """)

            rows = cur.fetchall()
            plans = {}

            for row in rows:
                # Map Stripe price IDs from environment variables (backwards compatibility)
                plan_key = row['plan_key']
                env_key_map = {
                    'starter_monthly': 'STRIPE_STARTER_MONTHLY_PRICE_ID',
                    'starter_annual': 'STRIPE_STARTER_ANNUAL_PRICE_ID',
                    'professional_monthly': 'STRIPE_PRO_MONTHLY_PRICE_ID',
                    'professional_annual': 'STRIPE_PRO_ANNUAL_PRICE_ID',
                    'business_monthly': 'STRIPE_BUSINESS_MONTHLY_PRICE_ID',
                    'business_annual': 'STRIPE_BUSINESS_ANNUAL_PRICE_ID',
                    'enterprise': 'STRIPE_ENTERPRISE_PRICE_ID'
                }

                plans[plan_key] = {
                    "name": row['name'],
                    "price_id": os.getenv(env_key_map.get(plan_key, '')) or row['stripe_price_id'],
                    "price": row['price'],
                    "currency": row['currency'],
                    "interval": row['interval'],
                    "credits": row['credits'],
                    "features": row['features'] if row['features'] else []
                }

            return plans

        finally:
            cur.close()


def get_credit_packages_from_db():
    """Fetch credit packages from database"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT package_key, name, price, currency, credits,
                       stripe_price_id, description, badge, price_per_credit, is_active
                FROM credit_packages
                WHERE is_active = true
                ORDER BY sort_order
            """)

            rows = cur.fetchall()
            packages = {}

            for row in rows:
                # Map Stripe price IDs from environment variables (backwards compatibility)
                package_key = row['package_key']
                env_key_map = {
                    'credits_500': 'STRIPE_CREDITS_500_PRICE_ID',
                    'credits_1000': 'STRIPE_CREDITS_1000_PRICE_ID',
                    'credits_2500': 'STRIPE_CREDITS_2500_PRICE_ID',
                    'credits_5000': 'STRIPE_CREDITS_5000_PRICE_ID'
                }

                package_data = {
                    "name": row['name'],
                    "price_id": os.getenv(env_key_map.get(package_key, '')) or row['stripe_price_id'],
                    "price": row['price'],
                    "currency": row['currency'],
                    "credits": row['credits'],
                    "description": row['description'],
                    "price_per_credit": float(row['price_per_credit']) if row['price_per_credit'] else 0
                }

                if row['badge']:
                    package_data['badge'] = row['badge']

                packages[package_key] = package_data

            return packages

        finally:
            cur.close()


class CheckoutRequest(BaseModel):
    plan: str  # starter, professional, enterprise


class CreditPurchaseRequest(BaseModel):
    package: str  # credits_500, credits_1000, credits_2500, credits_5000


@router.get("/payment/plans")
async def get_pricing_plans():
    """Get available pricing plans (from database)"""
    try:
        plans = get_pricing_plans_from_db()
        return {
            "success": True,
            "plans": plans
        }
    except Exception as e:
        logger.error(f"Error fetching pricing plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pricing plans")


@router.get("/payment/credit-packages")
async def get_credit_packages():
    """Get available credit top-up packages (from database)"""
    try:
        packages = get_credit_packages_from_db()
        return {
            "success": True,
            "packages": packages
        }
    except Exception as e:
        logger.error(f"Error fetching credit packages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch credit packages")


@router.post("/payment/purchase-credits")
async def purchase_credits(data: CreditPurchaseRequest, request: Request):
    """
    Create Stripe checkout session for credit purchase (one-time payment)

    This is different from subscriptions - it's a one-time payment that adds
    credits to the user's balance immediately after payment.
    """
    try:
        user_id = get_user_from_token(request)

        # Fetch packages from database
        packages = get_credit_packages_from_db()

        if data.package not in packages:
            raise HTTPException(status_code=400, detail="Invalid credit package selected")

        package = packages[data.package]
        price_id = package["price_id"]

        if not price_id:
            raise HTTPException(status_code=500, detail=f"Price ID not configured for {data.package}")

        # Get user email
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT email, name, stripe_customer_id FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create or reuse Stripe customer
        if user['stripe_customer_id']:
            customer_id = user['stripe_customer_id']
        else:
            customer = stripe.Customer.create(
                email=user['email'],
                name=user['name'],
                metadata={"user_id": user_id}
            )
            customer_id = customer.id

            # Save customer ID
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE users SET stripe_customer_id = %s WHERE id = %s", (customer_id, user_id))
                conn.commit()
                cur.close()

        # Create Checkout Session for ONE-TIME payment
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',  # ONE-TIME payment (not subscription)
            success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&type=credits",
            cancel_url=f"{FRONTEND_URL}/dashboard",
            metadata={
                "user_id": user_id,
                "package": data.package,
                "credits": package["credits"],
                "purchase_type": "credit_topup"
            }
        )

        logger.info(f"✅ Created credit purchase checkout for user {user_id}: {package['credits']} credits")

        return {
            "success": True,
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "credits": package["credits"]
        }

    except stripe.error.StripeError as e:
        logger.error(f"❌ Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment processing error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating credit purchase checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/payment/create-checkout")
async def create_checkout_session(data: CheckoutRequest, request: Request):
    """
    Create Stripe checkout session for a plan

    This redirects the user to Stripe's hosted checkout page
    """
    try:
        user_id = get_user_from_token(request)

        # Fetch plans from database
        plans = get_pricing_plans_from_db()

        if data.plan not in plans:
            raise HTTPException(status_code=400, detail="Invalid plan selected")

        plan = plans[data.plan]
        price_id = plan["price_id"]

        if not price_id:
            raise HTTPException(status_code=500, detail=f"Price ID not configured for {data.plan} plan")

        # Get user email
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT email, name, stripe_customer_id FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create or reuse Stripe customer
        if user['stripe_customer_id']:
            customer_id = user['stripe_customer_id']
        else:
            customer = stripe.Customer.create(
                email=user['email'],
                name=user['name'],
                metadata={"user_id": user_id}
            )
            customer_id = customer.id

            # Save customer ID
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE users SET stripe_customer_id = %s WHERE id = %s", (customer_id, user_id))
                conn.commit()
                cur.close()

        # Create Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/payment/canceled",
            metadata={
                "user_id": user_id,
                "plan": data.plan
            },
            subscription_data={
                "metadata": {
                    "user_id": user_id,
                    "plan": data.plan
                }
            }
        )

        logger.info(f"✅ Created checkout session for user {user_id}: {checkout_session.id}")

        return {
            "success": True,
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }

    except stripe.error.StripeError as e:
        logger.error(f"❌ Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment processing error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/payment/status")
async def get_payment_status(request: Request):
    """Get current user's payment/subscription status"""
    try:
        user_id = get_user_from_token(request)

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT plan, subscription_status, stripe_subscription_id,
                       subscription_started_at, subscription_ends_at
                FROM users WHERE id = %s
            """, (user_id,))
            user = cur.fetchone()
            cur.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "payment_status": {
                "plan": user['plan'],
                "subscription_status": user['subscription_status'] or 'inactive',
                "has_paid": user['plan'] != 'free',
                "subscription_started_at": user['subscription_started_at'].isoformat() if user['subscription_started_at'] else None,
                "subscription_ends_at": user['subscription_ends_at'].isoformat() if user['subscription_ends_at'] else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting payment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get payment status")


@router.post("/payment/create-portal-session")
async def create_customer_portal_session(request: Request):
    """
    Create Stripe Customer Portal session

    This allows users to:
    - Update payment methods
    - View billing history
    - Cancel subscription
    - Update subscription
    """
    try:
        user_id = get_user_from_token(request)

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT stripe_customer_id FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user['stripe_customer_id']:
            raise HTTPException(status_code=400, detail="No Stripe customer ID found. Please complete a payment first.")

        # Create Customer Portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=user['stripe_customer_id'],
            return_url=f"{FRONTEND_URL}/dashboard/settings",
        )

        logger.info(f"✅ Created Customer Portal session for user {user_id}")

        return {
            "success": True,
            "portal_url": portal_session.url
        }

    except stripe.error.StripeError as e:
        logger.error(f"❌ Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment processing error")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/payment/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Handle Stripe webhooks with idempotency

    This endpoint receives events from Stripe when:
    - Payment succeeds
    - Subscription is created
    - Subscription is canceled
    - Payment fails

    IDEMPOTENCY: Each event_id is processed exactly once to prevent zombie subscriptions.
    """
    try:
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("❌ Invalid webhook payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("❌ Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

        event_id = event['id']
        event_type = event['type']
        logger.info(f"📨 Received Stripe webhook: {event_type} ({event_id})")

        # IDEMPOTENCY CHECK: Skip if already processed
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT is_webhook_event_processed(%s) as is_processed",
                (event_id,)
            )
            result = cur.fetchone()
            already_processed = result['is_processed'] if result else False
            cur.close()

        if already_processed:
            logger.info(f"⏭️  Skipping already processed event: {event_id}")
            return {"success": True, "message": "Event already processed (idempotent skip)"}

        # Process the event
        try:
            # Handle different event types
            user_id = None

            if event_type == 'checkout.session.completed':
                session = event['data']['object']
                user_id = session.get('metadata', {}).get('user_id')
                await handle_checkout_success(session)

            elif event_type == 'customer.subscription.created':
                subscription = event['data']['object']
                user_id = subscription.get('metadata', {}).get('user_id')
                await handle_subscription_created(subscription)

            elif event_type == 'customer.subscription.updated':
                subscription = event['data']['object']
                user_id = subscription.get('metadata', {}).get('user_id')
                await handle_subscription_updated(subscription)

            elif event_type == 'customer.subscription.deleted':
                subscription = event['data']['object']
                user_id = subscription.get('metadata', {}).get('user_id')
                await handle_subscription_canceled(subscription)

            elif event_type == 'invoice.payment_failed':
                invoice = event['data']['object']
                # user_id not easily available from invoice
                await handle_payment_failed(invoice)

            # Record successful processing
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT record_webhook_event(%s, %s, %s, %s, %s, %s)",
                    (event_id, event_type, psycopg2.extras.Json(event), 'success', None, user_id)
                )
                conn.commit()
                cur.close()

            logger.info(f"✅ Successfully processed webhook: {event_id}")
            return {"success": True, "event_id": event_id}

        except Exception as processing_error:
            # Record failed processing
            error_message = str(processing_error)
            logger.error(f"❌ Error processing webhook {event_id}: {error_message}")

            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT record_webhook_event(%s, %s, %s, %s, %s, %s)",
                    (event_id, event_type, psycopg2.extras.Json(event), 'error', error_message, user_id)
                )
                conn.commit()
                cur.close()

            raise processing_error

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing error")


async def handle_checkout_success(session):
    """Handle successful checkout session (subscription OR credit purchase)"""
    user_id = session['metadata']['user_id']
    customer_id = session['customer']

    # Check if this is a credit purchase or subscription
    purchase_type = session['metadata'].get('purchase_type')

    if purchase_type == 'credit_topup':
        # Handle credit purchase
        credits = int(session['metadata']['credits'])
        package = session['metadata']['package']
        payment_intent_id = session.get('payment_intent')

        logger.info(f"💳 Credit purchase completed for user {user_id}: {credits} credits")

        try:
            # Add credits to user's balance
            result = add_credits(
                user_id=user_id,
                credits=credits,
                transaction_type='purchased',
                description=f"Purchased {credits} credits ({package})",
                stripe_payment_intent_id=payment_intent_id
            )

            logger.info(f"✅ Added {credits} credits to user {user_id}. New balance: {result['balance_after']}")

        except Exception as e:
            logger.error(f"❌ Failed to add credits for user {user_id}: {str(e)}")
            raise

    else:
        # Handle subscription checkout
        plan = session['metadata']['plan']
        subscription_id = session['subscription']

        logger.info(f"💳 Subscription checkout completed for user {user_id}: {plan} plan")

        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE users
                    SET plan = %s,
                        stripe_customer_id = %s,
                        stripe_subscription_id = %s,
                        subscription_status = 'active',
                        subscription_started_at = NOW()
                    WHERE id = %s
                """, (plan, customer_id, subscription_id, user_id))

                conn.commit()
                logger.info(f"✅ Updated user {user_id} to {plan} plan")

            finally:
                cur.close()


async def handle_subscription_created(subscription):
    """Handle subscription creation"""
    user_id = subscription['metadata']['user_id']
    subscription_id = subscription['id']
    status = subscription['status']

    logger.info(f"📝 Subscription created for user {user_id}: {subscription_id}")

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users
                SET stripe_subscription_id = %s,
                    subscription_status = %s
                WHERE id = %s
            """, (subscription_id, status, user_id))

            conn.commit()

        finally:
            cur.close()


async def handle_subscription_updated(subscription):
    """Handle subscription updates (renewals, plan changes, etc.)"""
    customer_id = subscription['customer']
    subscription_id = subscription['id']
    status = subscription['status']

    logger.info(f"🔄 Subscription updated: {subscription_id} - Status: {status}")

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users
                SET subscription_status = %s
                WHERE stripe_customer_id = %s
            """, (status, customer_id))

            conn.commit()

        finally:
            cur.close()


async def handle_subscription_canceled(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription['customer']

    logger.info(f"❌ Subscription canceled for customer: {customer_id}")

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users
                SET subscription_status = 'canceled',
                    plan = 'free'
                WHERE stripe_customer_id = %s
            """, (customer_id,))

            conn.commit()

        finally:
            cur.close()


async def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice['customer']

    logger.warning(f"⚠️  Payment failed for customer: {customer_id}")

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users
                SET subscription_status = 'past_due'
                WHERE stripe_customer_id = %s
            """, (customer_id,))

            conn.commit()

        finally:
            cur.close()
