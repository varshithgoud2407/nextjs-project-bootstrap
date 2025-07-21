from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import stripe
import logging
from datetime import datetime

from database import get_db
from models import User, Payment
from dependencies import get_current_active_user
from config import settings
from exceptions import PaymentException

logger = logging.getLogger(__name__)

router = APIRouter()

# Configure Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

# Payment plans
PAYMENT_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "currency": "usd",
        "features": [
            "30 minutes AI conversation per week",
            "Text-based chat only",
            "Basic emotional support",
            "Limited language support"
        ],
        "limits": {
            "weekly_minutes": 30,
            "voice_messages": False,
            "video_calls": False,
            "priority_support": False
        }
    },
    "premium": {
        "name": "Premium",
        "price": 9.99,
        "currency": "usd",
        "stripe_price_id": "price_premium_monthly",  # Replace with actual Stripe price ID
        "features": [
            "Unlimited AI voice conversations",
            "All languages supported",
            "Video call integration",
            "Advanced emotional intelligence",
            "Priority support",
            "Conversation history"
        ],
        "limits": {
            "weekly_minutes": -1,  # Unlimited
            "voice_messages": True,
            "video_calls": True,
            "priority_support": True
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 29.99,
        "currency": "usd",
        "stripe_price_id": "price_enterprise_monthly",  # Replace with actual Stripe price ID
        "features": [
            "Everything in Premium",
            "Custom AI personality",
            "Integration with corporate wellness",
            "Analytics and reporting",
            "24/7 priority support",
            "Team management",
            "Custom branding"
        ],
        "limits": {
            "weekly_minutes": -1,  # Unlimited
            "voice_messages": True,
            "video_calls": True,
            "priority_support": True,
            "analytics": True,
            "team_management": True
        }
    }
}

# Pydantic models
class PaymentPlanResponse(BaseModel):
    plan_id: str
    name: str
    price: float
    currency: str
    features: List[str]

class CheckoutRequest(BaseModel):
    plan_type: str
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

class PaymentResponse(BaseModel):
    id: int
    amount: float
    currency: str
    plan_type: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubscriptionStatus(BaseModel):
    is_premium: bool
    current_plan: str
    plan_details: dict
    usage: dict

@router.get("/plans", response_model=List[PaymentPlanResponse])
async def get_payment_plans():
    """Get available payment plans"""
    plans = []
    for plan_id, plan_data in PAYMENT_PLANS.items():
        plans.append(PaymentPlanResponse(
            plan_id=plan_id,
            name=plan_data["name"],
            price=plan_data["price"],
            currency=plan_data["currency"],
            features=plan_data["features"]
        ))
    return plans

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    checkout_request: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session"""
    try:
        if not settings.STRIPE_API_KEY:
            raise PaymentException("Payment processing is not configured")
        
        plan = PAYMENT_PLANS.get(checkout_request.plan_type)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan type"
            )
        
        if checkout_request.plan_type == "free":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Free plan doesn't require payment"
            )
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan["stripe_price_id"],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=checkout_request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=checkout_request.cancel_url,
            customer_email=current_user.email,
            metadata={
                'user_id': str(current_user.id),
                'plan_type': checkout_request.plan_type
            }
        )
        
        # Create payment record
        payment = Payment(
            user_id=current_user.id,
            stripe_payment_id=checkout_session.id,
            amount=plan["price"],
            currency=plan["currency"],
            plan_type=checkout_request.plan_type,
            status="pending"
        )
        
        db.add(payment)
        db.commit()
        
        logger.info(f"Checkout session created for user {current_user.id}, plan: {checkout_request.plan_type}")
        
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise PaymentException(f"Payment processing error: {str(e)}")
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise HTTPException(status_code=400, detail="Webhook secret not configured")
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await handle_successful_payment(session, db)
        
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            await handle_subscription_renewal(invoice, db)
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await handle_subscription_cancelled(subscription, db)
        
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return {"status": "success"}
        
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def handle_successful_payment(session, db: Session):
    """Handle successful payment"""
    try:
        user_id = int(session['metadata']['user_id'])
        plan_type = session['metadata']['plan_type']
        
        # Update payment record
        payment = db.query(Payment).filter(
            Payment.stripe_payment_id == session['id']
        ).first()
        
        if payment:
            payment.status = "completed"
            
            # Update user to premium
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_premium = True
                
                logger.info(f"User {user_id} upgraded to {plan_type}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error handling successful payment: {e}")
        db.rollback()

async def handle_subscription_renewal(invoice, db: Session):
    """Handle subscription renewal"""
    try:
        # This would handle recurring subscription payments
        logger.info(f"Subscription renewed: {invoice['id']}")
        
    except Exception as e:
        logger.error(f"Error handling subscription renewal: {e}")

async def handle_subscription_cancelled(subscription, db: Session):
    """Handle subscription cancellation"""
    try:
        # Find user by customer ID and downgrade
        customer_id = subscription['customer']
        
        # You would need to store customer_id in user record to match
        # For now, log the cancellation
        logger.info(f"Subscription cancelled: {subscription['id']}")
        
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")

@router.get("/subscription-status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's subscription status"""
    try:
        # Determine current plan
        current_plan = "premium" if current_user.is_premium else "free"
        plan_details = PAYMENT_PLANS[current_plan]
        
        # Get usage statistics (placeholder)
        usage = {
            "weekly_minutes_used": 0,  # Would calculate from AI sessions
            "total_sessions": 0,       # Would count from database
            "voice_messages_sent": 0   # Would count from messages
        }
        
        return SubscriptionStatus(
            is_premium=current_user.is_premium,
            current_plan=current_plan,
            plan_details=plan_details,
            usage=usage
        )
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription status"
        )

@router.get("/payment-history", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's payment history"""
    try:
        payments = db.query(Payment).filter(
            Payment.user_id == current_user.id
        ).order_by(Payment.created_at.desc()).all()
        
        return [PaymentResponse.from_orm(payment) for payment in payments]
        
    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment history"
        )

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel user's subscription"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription to cancel"
            )
        
        # In a real implementation, you would:
        # 1. Find the Stripe subscription ID
        # 2. Cancel it via Stripe API
        # 3. Update user status
        
        # For now, just downgrade the user
        current_user.is_premium = False
        db.commit()
        
        logger.info(f"Subscription cancelled for user {current_user.id}")
        
        return {"message": "Subscription cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )
