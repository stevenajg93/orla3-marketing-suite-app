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

router = APIRouter()
logger = setup_logger(__name__)

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

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

# Pricing Plans (matches landing page pricing)
PRICING_PLANS = {
    "starter_monthly": {
        "name": "Starter",
        "price_id": os.getenv("STRIPE_STARTER_MONTHLY_PRICE_ID"),
        "price": 99,
        "currency": "GBP",
        "interval": "month",
        "credits": 500,
        "features": [
            "500 credits/month",
            "~100 social captions or 50 blog posts",
            "25 AI-generated ultra images",
            "2 AI-generated videos (8-sec)",
            "1 brand voice profile",
            "3 social accounts",
            "Content calendar",
            "Basic competitor tracking (2 competitors)",
            "Credit rollover (up to 250)"
        ]
    },
    "starter_annual": {
        "name": "Starter (Annual)",
        "price_id": os.getenv("STRIPE_STARTER_ANNUAL_PRICE_ID"),
        "price": 990,
        "currency": "GBP",
        "interval": "year",
        "credits": 500,
        "features": [
            "500 credits/month",
            "2 months FREE (annual billing)",
            "~100 social captions or 50 blog posts",
            "25 AI-generated ultra images",
            "2 AI-generated videos (8-sec)",
            "1 brand voice profile",
            "3 social accounts",
            "Content calendar",
            "Basic competitor tracking (2 competitors)",
            "Credit rollover (up to 250)"
        ]
    },
    "professional_monthly": {
        "name": "Professional",
        "price_id": os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID"),
        "price": 249,
        "currency": "GBP",
        "interval": "month",
        "credits": 2000,
        "features": [
            "2,000 credits/month",
            "~400 social posts or 200 blog posts",
            "100 AI-generated ultra images",
            "10 AI-generated videos (8-sec)",
            "3 brand voice profiles",
            "10 social accounts",
            "Auto-publishing & scheduling",
            "Advanced competitor analysis (5 competitors)",
            "Priority support",
            "Credit rollover (up to 1,000)"
        ]
    },
    "professional_annual": {
        "name": "Professional (Annual)",
        "price_id": os.getenv("STRIPE_PRO_ANNUAL_PRICE_ID"),
        "price": 2490,
        "currency": "GBP",
        "interval": "year",
        "credits": 2000,
        "features": [
            "2,000 credits/month",
            "2 months FREE (annual billing)",
            "~400 social posts or 200 blog posts",
            "100 AI-generated ultra images",
            "10 AI-generated videos (8-sec)",
            "3 brand voice profiles",
            "10 social accounts",
            "Auto-publishing & scheduling",
            "Advanced competitor analysis (5 competitors)",
            "Priority support",
            "Credit rollover (up to 1,000)"
        ]
    },
    "business_monthly": {
        "name": "Business",
        "price_id": os.getenv("STRIPE_BUSINESS_MONTHLY_PRICE_ID"),
        "price": 499,
        "currency": "GBP",
        "interval": "month",
        "credits": 6000,
        "features": [
            "6,000 credits/month",
            "~1,200 social posts or 600 blog posts",
            "300 AI-generated ultra images",
            "30 AI-generated videos (8-sec)",
            "10 brand voice profiles",
            "25 social accounts",
            "Multi-user collaboration (5 seats)",
            "Unlimited competitor tracking",
            "API access",
            "White-label options",
            "Credit rollover (up to 3,000)"
        ]
    },
    "business_annual": {
        "name": "Business (Annual)",
        "price_id": os.getenv("STRIPE_BUSINESS_ANNUAL_PRICE_ID"),
        "price": 4990,
        "currency": "GBP",
        "interval": "year",
        "credits": 6000,
        "features": [
            "6,000 credits/month",
            "2 months FREE (annual billing)",
            "~1,200 social posts or 600 blog posts",
            "300 AI-generated ultra images",
            "30 AI-generated videos (8-sec)",
            "10 brand voice profiles",
            "25 social accounts",
            "Multi-user collaboration (5 seats)",
            "Unlimited competitor tracking",
            "API access",
            "White-label options",
            "Credit rollover (up to 3,000)"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID"),
        "price": 999,
        "currency": "GBP",
        "interval": "month",
        "credits": 20000,
        "features": [
            "20,000 credits/month",
            "~4,000 social posts or 2,000 blog posts",
            "1,000 AI-generated ultra images",
            "100 AI-generated videos (8-sec)",
            "Unlimited brand voices",
            "Unlimited social accounts",
            "Unlimited team members",
            "Dedicated account manager",
            "Custom integrations",
            "SLA guarantees",
            "Full credit rollover"
        ]
    }
}


class CheckoutRequest(BaseModel):
    plan: str  # starter, professional, enterprise


@router.get("/payment/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    return {
        "success": True,
        "plans": PRICING_PLANS
    }


@router.post("/payment/create-checkout")
async def create_checkout_session(data: CheckoutRequest, request: Request):
    """
    Create Stripe checkout session for a plan

    This redirects the user to Stripe's hosted checkout page
    """
    try:
        user_id = get_user_from_token(request)

        if data.plan not in PRICING_PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan selected")

        plan = PRICING_PLANS[data.plan]
        price_id = plan["price_id"]

        if not price_id:
            raise HTTPException(status_code=500, detail=f"Price ID not configured for {data.plan} plan")

        # Get user email
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT email, name, stripe_customer_id FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()

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
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET stripe_customer_id = %s WHERE id = %s", (customer_id, user_id))
            conn.commit()
            cur.close()
            conn.close()

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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error creating checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment/status")
async def get_payment_status(request: Request):
    """Get current user's payment/subscription status"""
    try:
        user_id = get_user_from_token(request)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT plan, subscription_status, stripe_subscription_id,
                   subscription_started_at, subscription_ends_at
            FROM users WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()

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

    except Exception as e:
        logger.error(f"❌ Error getting payment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payment/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Handle Stripe webhooks

    This endpoint receives events from Stripe when:
    - Payment succeeds
    - Subscription is created
    - Subscription is canceled
    - Payment fails
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

        event_type = event['type']
        logger.info(f"📨 Received Stripe webhook: {event_type}")

        # Handle different event types
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            await handle_checkout_success(session)

        elif event_type == 'customer.subscription.created':
            subscription = event['data']['object']
            await handle_subscription_created(subscription)

        elif event_type == 'customer.subscription.updated':
            subscription = event['data']['object']
            await handle_subscription_updated(subscription)

        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await handle_subscription_canceled(subscription)

        elif event_type == 'invoice.payment_failed':
            invoice = event['data']['object']
            await handle_payment_failed(invoice)

        return {"success": True}

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_checkout_success(session):
    """Handle successful checkout session"""
    user_id = session['metadata']['user_id']
    plan = session['metadata']['plan']
    customer_id = session['customer']
    subscription_id = session['subscription']

    logger.info(f"💳 Checkout completed for user {user_id}: {plan} plan")

    conn = get_db_connection()
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
        conn.close()


async def handle_subscription_created(subscription):
    """Handle subscription creation"""
    user_id = subscription['metadata']['user_id']
    subscription_id = subscription['id']
    status = subscription['status']

    logger.info(f"📝 Subscription created for user {user_id}: {subscription_id}")

    conn = get_db_connection()
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
        conn.close()


async def handle_subscription_updated(subscription):
    """Handle subscription updates (renewals, plan changes, etc.)"""
    customer_id = subscription['customer']
    subscription_id = subscription['id']
    status = subscription['status']

    logger.info(f"🔄 Subscription updated: {subscription_id} - Status: {status}")

    conn = get_db_connection()
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
        conn.close()


async def handle_subscription_canceled(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription['customer']

    logger.info(f"❌ Subscription canceled for customer: {customer_id}")

    conn = get_db_connection()
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
        conn.close()


async def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice['customer']

    logger.warning(f"⚠️  Payment failed for customer: {customer_id}")

    conn = get_db_connection()
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
        conn.close()
