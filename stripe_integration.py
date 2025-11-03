#!/usr/bin/env python3
"""
Stripe payment integration for SousSpeed Pro Chef subscriptions.
"""

import os
import stripe
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from firebase_models import FirebaseManager, SubscriptionStatus, PlanType

# Initialize Stripe with secret key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')  # Use your test key

# Stripe configuration
STRIPE_CONFIG = {
    'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_...'),  # Use your test key
    'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_...'),     # Use your webhook secret
    'pro_chef_price_id': os.getenv('STRIPE_PRO_CHEF_PRICE_ID', 'price_...'), # Your product price ID
    'currency': 'usd',
    'trial_days': 7
}

class StripePaymentManager:
    """Manages Stripe payments and subscriptions for SousSpeed."""
    
    def __init__(self, firebase_manager: FirebaseManager):
        """Initialize payment manager with Firebase."""
        self.db = firebase_manager
    
    def create_checkout_session(self, user_uid: str, plan_type: str = 'pro_chef',
                              success_url: str = '', cancel_url: str = '',
                              trial_days: int = 7) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription.
        
        Args:
            user_uid: User UID from Firebase
            plan_type: Subscription plan type
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            trial_days: Number of trial days (0 for no trial)
            
        Returns:
            Dictionary with checkout session details
        """
        try:
            user = self.db.get_user_profile(user_uid)
            if not user:
                return {'error': 'User not found'}
            
            # Create or retrieve Stripe customer
            stripe_customer = self.get_or_create_stripe_customer(user)
            
            # Checkout session parameters
            session_params = {
                'customer': stripe_customer.id,
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': STRIPE_CONFIG['pro_chef_price_id'],
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url + '?session_id={CHECKOUT_SESSION_ID}',
                'cancel_url': cancel_url,
                'metadata': {
                    'user_uid': user_uid,
                    'plan_type': plan_type
                },
                'subscription_data': {
                    'metadata': {
                        'user_uid': user_uid,
                        'plan_type': plan_type
                    }
                }
            }
            
            # Add trial period if specified
            if trial_days > 0:
                session_params['subscription_data']['trial_period_days'] = trial_days
            
            # Create checkout session
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id,
                'customer_id': stripe_customer.id
            }
            
        except stripe.error.StripeError as e:
            return {'error': f'Stripe error: {str(e)}'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}
    
    def create_payment_intent(self, user_id: int, amount: int,
                            currency: str = 'usd', 
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a PaymentIntent for one-time payments.
        
        Args:
            user_id: User ID from database
            amount: Amount in cents
            currency: Currency code
            metadata: Additional metadata
            
        Returns:
            Dictionary with PaymentIntent details
        """
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Create or retrieve Stripe customer
            stripe_customer = self.get_or_create_stripe_customer(user)
            
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=stripe_customer.id,
                metadata={
                    'user_id': str(user_id),
                    'user_email': user.email,
                    **(metadata or {})
                },
                automatic_payment_methods={'enabled': True}
            )
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'customer_id': stripe_customer.id
            }
            
        except stripe.error.StripeError as e:
            return {'error': f'Stripe error: {str(e)}'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}
    
    def get_or_create_stripe_customer(self, user) -> stripe.Customer:
        """Get existing or create new Stripe customer for user."""
        # Check if user already has a Stripe customer
        subscription = self.db.get_user_subscription(user.id)
        
        if subscription and subscription.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(subscription.stripe_customer_id)
                return customer
            except stripe.error.InvalidRequestError:
                # Customer doesn't exist, create new one
                pass
        
        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            metadata={
                'user_id': str(user.id),
                'created_at': datetime.now().isoformat()
            }
        )
        
        return customer
    
    def handle_successful_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Handle successful payment and activate subscription."""
        try:
            # Retrieve PaymentIntent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status != 'succeeded':
                return {'error': 'Payment not successful'}
            
            user_id = int(intent.metadata.get('user_id'))
            if not user_id:
                return {'error': 'User ID not found in payment metadata'}
            
            # Create Pro Chef subscription
            subscription = self.db.create_subscription(
                user_id=user_id,
                plan_type=PlanType.PRO_CHEF.value,
                stripe_customer_id=intent.customer,
                is_trial=False
            )
            
            if not subscription:
                return {'error': 'Failed to create subscription'}
            
            # Record payment
            payment_record = self.db.create_payment_record(
                user_id=user_id,
                subscription_id=subscription.id,
                stripe_payment_intent_id=payment_intent_id,
                amount=intent.amount,
                currency=intent.currency,
                status='succeeded',
                metadata={
                    'stripe_charge_id': intent.charges.data[0].id if intent.charges.data else None,
                    'payment_method': intent.charges.data[0].payment_method_details.type if intent.charges.data else None
                }
            )
            
            return {
                'success': True,
                'subscription': subscription,
                'payment': payment_record,
                'message': 'Pro Chef subscription activated successfully!'
            }
            
        except Exception as e:
            return {'error': f'Error processing successful payment: {str(e)}'}
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        
        Args:
            payload: Raw webhook payload
            sig_header: Stripe signature header
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_CONFIG['webhook_secret']
            )
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self.handle_checkout_completed(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.created':
                return self.handle_subscription_created(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.updated':
                return self.handle_subscription_updated(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.deleted':
                return self.handle_subscription_deleted(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_succeeded':
                return self.handle_invoice_payment_succeeded(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_failed':
                return self.handle_invoice_payment_failed(event['data']['object'])
            
            else:
                return {'success': True, 'message': f'Unhandled event type: {event["type"]}'}
                
        except stripe.error.SignatureVerificationError:
            return {'error': 'Invalid webhook signature'}
        except Exception as e:
            return {'error': f'Webhook processing error: {str(e)}'}
    
    def handle_checkout_completed(self, session) -> Dict[str, Any]:
        """Handle successful checkout session completion."""
        try:
            user_id = int(session['metadata']['user_id'])
            plan_type = session['metadata']['plan_type']
            
            # Retrieve the subscription from Stripe
            stripe_subscription = stripe.Subscription.retrieve(session['subscription'])
            
            # Determine if this is a trial
            is_trial = stripe_subscription.trial_end is not None
            
            # Create subscription in database
            subscription = self.db.create_subscription(
                user_id=user_id,
                plan_type=plan_type,
                stripe_customer_id=session['customer'],
                stripe_subscription_id=session['subscription'],
                is_trial=is_trial
            )
            
            return {
                'success': True,
                'message': 'Subscription created successfully',
                'subscription_id': subscription.id if subscription else None
            }
            
        except Exception as e:
            return {'error': f'Error handling checkout completion: {str(e)}'}
    
    def handle_subscription_created(self, subscription) -> Dict[str, Any]:
        """Handle subscription creation from Stripe."""
        try:
            user_id = int(subscription['metadata']['user_id'])
            
            # Update subscription with Stripe details
            db_subscription = self.db.get_user_subscription(user_id)
            if db_subscription:
                # Update subscription status based on Stripe subscription
                status = SubscriptionStatus.TRIAL.value if subscription['trial_end'] else SubscriptionStatus.ACTIVE.value
                
                self.db.update_subscription_status(
                    db_subscription.id,
                    status,
                    metadata={
                        'stripe_status': subscription['status'],
                        'current_period_start': subscription['current_period_start'],
                        'current_period_end': subscription['current_period_end']
                    }
                )
            
            return {'success': True, 'message': 'Subscription updated with Stripe details'}
            
        except Exception as e:
            return {'error': f'Error handling subscription creation: {str(e)}'}
    
    def handle_subscription_updated(self, subscription) -> Dict[str, Any]:
        """Handle subscription updates from Stripe."""
        try:
            db_subscription = self.db.get_subscription_by_stripe_id(subscription['id'])
            
            if db_subscription:
                # Map Stripe status to our status
                status_map = {
                    'active': SubscriptionStatus.ACTIVE.value,
                    'trialing': SubscriptionStatus.TRIAL.value,
                    'canceled': SubscriptionStatus.CANCELLED.value,
                    'incomplete': SubscriptionStatus.PENDING.value,
                    'past_due': SubscriptionStatus.EXPIRED.value
                }
                
                new_status = status_map.get(subscription['status'], SubscriptionStatus.EXPIRED.value)
                
                self.db.update_subscription_status(
                    db_subscription.id,
                    new_status,
                    metadata={
                        'stripe_status': subscription['status'],
                        'current_period_start': subscription['current_period_start'],
                        'current_period_end': subscription['current_period_end'],
                        'cancel_at_period_end': subscription.get('cancel_at_period_end', False)
                    }
                )
            
            return {'success': True, 'message': 'Subscription status updated'}
            
        except Exception as e:
            return {'error': f'Error handling subscription update: {str(e)}'}
    
    def handle_subscription_deleted(self, subscription) -> Dict[str, Any]:
        """Handle subscription cancellation from Stripe."""
        try:
            db_subscription = self.db.get_subscription_by_stripe_id(subscription['id'])
            
            if db_subscription:
                self.db.update_subscription_status(
                    db_subscription.id,
                    SubscriptionStatus.CANCELLED.value,
                    metadata={
                        'stripe_status': 'canceled',
                        'cancelled_at': subscription.get('canceled_at'),
                        'cancellation_reason': 'stripe_cancellation'
                    }
                )
            
            return {'success': True, 'message': 'Subscription cancelled'}
            
        except Exception as e:
            return {'error': f'Error handling subscription deletion: {str(e)}'}
    
    def handle_invoice_payment_succeeded(self, invoice) -> Dict[str, Any]:
        """Handle successful invoice payment."""
        try:
            subscription_id = invoice['subscription']
            db_subscription = self.db.get_subscription_by_stripe_id(subscription_id)
            
            if db_subscription:
                # Record successful payment
                payment_record = self.db.create_payment_record(
                    user_id=db_subscription.user_id,
                    subscription_id=db_subscription.id,
                    stripe_payment_intent_id=invoice['payment_intent'],
                    amount=invoice['amount_paid'],
                    currency=invoice['currency'],
                    status='succeeded',
                    metadata={
                        'invoice_id': invoice['id'],
                        'billing_reason': invoice['billing_reason']
                    }
                )
                
                # Ensure subscription is active
                self.db.update_subscription_status(
                    db_subscription.id,
                    SubscriptionStatus.ACTIVE.value
                )
            
            return {'success': True, 'message': 'Payment recorded successfully'}
            
        except Exception as e:
            return {'error': f'Error handling successful payment: {str(e)}'}
    
    def handle_invoice_payment_failed(self, invoice) -> Dict[str, Any]:
        """Handle failed invoice payment."""
        try:
            subscription_id = invoice['subscription']
            db_subscription = self.db.get_subscription_by_stripe_id(subscription_id)
            
            if db_subscription:
                # Record failed payment attempt
                if invoice['payment_intent']:
                    payment_record = self.db.create_payment_record(
                        user_id=db_subscription.user_id,
                        subscription_id=db_subscription.id,
                        stripe_payment_intent_id=invoice['payment_intent'],
                        amount=invoice['amount_due'],
                        currency=invoice['currency'],
                        status='failed',
                        metadata={
                            'invoice_id': invoice['id'],
                            'billing_reason': invoice['billing_reason'],
                            'failure_reason': 'payment_failed'
                        }
                    )
                
                # Update subscription status to expired if payment failed
                self.db.update_subscription_status(
                    db_subscription.id,
                    SubscriptionStatus.EXPIRED.value,
                    metadata={'payment_failure': True}
                )
            
            return {'success': True, 'message': 'Payment failure recorded'}
            
        except Exception as e:
            return {'error': f'Error handling payment failure: {str(e)}'}
    
    def cancel_subscription(self, user_id: int, immediately: bool = False) -> Dict[str, Any]:
        """Cancel user's subscription."""
        try:
            subscription = self.db.get_user_subscription(user_id)
            
            if not subscription or not subscription.stripe_subscription_id:
                return {'error': 'No active subscription found'}
            
            # Cancel in Stripe
            if immediately:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
            else:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            # Update local database
            status = SubscriptionStatus.CANCELLED.value if immediately else SubscriptionStatus.ACTIVE.value
            self.db.update_subscription_status(
                subscription.id,
                status,
                metadata={'cancel_at_period_end': not immediately}
            )
            
            return {
                'success': True,
                'message': 'Subscription cancelled successfully',
                'immediate': immediately
            }
            
        except Exception as e:
            return {'error': f'Error cancelling subscription: {str(e)}'}
    
    def get_subscription_status(self, user_id: int) -> Dict[str, Any]:
        """Get detailed subscription status for user."""
        try:
            user = self.db.get_user_by_id(user_id)
            subscription = self.db.get_user_subscription(user_id)
            
            if not subscription:
                return {
                    'plan_type': 'free',
                    'status': 'none',
                    'has_access': False,
                    'features': ['beef']
                }
            
            # Check access to features
            has_access = self.db.check_user_access(user_id, 'chicken')  # Test with premium feature
            
            # Determine available features
            if subscription.plan_type == PlanType.PRO_CHEF.value and has_access:
                features = ['beef', 'chicken', 'pork', 'fish', 'vegetables']
            else:
                features = ['beef']
            
            return {
                'plan_type': subscription.plan_type,
                'status': subscription.status,
                'has_access': has_access,
                'features': features,
                'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                'period_end': subscription.period_end.isoformat() if subscription.period_end else None,
                'stripe_subscription_id': subscription.stripe_subscription_id
            }
            
        except Exception as e:
            return {'error': f'Error getting subscription status: {str(e)}'}


# Initialize payment manager
def get_payment_manager() -> StripePaymentManager:
    """Get initialized payment manager."""
    from models import db
    return StripePaymentManager(db)
