#!/usr/bin/env python3
"""
Firebase integration for SousSpeed user management and subscriptions.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dataclasses import dataclass, asdict
from enum import Enum


class SubscriptionStatus(Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class PlanType(Enum):
    """Subscription plan types."""
    FREE = "free"
    PRO_CHEF = "pro_chef"


@dataclass
class User:
    """User data model for Firebase."""
    uid: str = ""
    email: str = ""
    name: str = ""
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_verified: bool = False
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore."""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at
        if self.last_login:
            data['last_login'] = self.last_login
        return data

    @classmethod
    def from_dict(cls, uid: str, data: Dict[str, Any]) -> 'User':
        """Create User from Firestore document."""
        return cls(
            uid=uid,
            email=data.get('email', ''),
            name=data.get('name', ''),
            created_at=data.get('created_at'),
            last_login=data.get('last_login'),
            is_verified=data.get('is_verified', False),
            metadata=data.get('metadata', {})
        )


@dataclass
class Subscription:
    """Subscription data model for Firebase."""
    id: Optional[str] = None
    user_uid: str = ""
    plan_type: str = PlanType.FREE.value
    status: str = SubscriptionStatus.EXPIRED.value
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore."""
        data = asdict(self)
        # Convert datetime objects to Firestore timestamps
        for field in ['trial_start', 'trial_end', 'period_start', 'period_end', 
                     'created_at', 'updated_at', 'cancelled_at']:
            if getattr(self, field):
                data[field] = getattr(self, field)
        return data

    @classmethod
    def from_dict(cls, doc_id: str, data: Dict[str, Any]) -> 'Subscription':
        """Create Subscription from Firestore document."""
        return cls(
            id=doc_id,
            user_uid=data.get('user_uid', ''),
            plan_type=data.get('plan_type', PlanType.FREE.value),
            status=data.get('status', SubscriptionStatus.EXPIRED.value),
            stripe_customer_id=data.get('stripe_customer_id'),
            stripe_subscription_id=data.get('stripe_subscription_id'),
            stripe_payment_intent_id=data.get('stripe_payment_intent_id'),
            trial_start=data.get('trial_start'),
            trial_end=data.get('trial_end'),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            cancelled_at=data.get('cancelled_at'),
            metadata=data.get('metadata', {})
        )


@dataclass
class PaymentRecord:
    """Payment transaction record for Firebase."""
    id: Optional[str] = None
    user_uid: str = ""
    subscription_id: Optional[str] = None
    stripe_payment_intent_id: str = ""
    stripe_charge_id: Optional[str] = None
    amount: int = 0  # Amount in cents
    currency: str = "usd"
    status: str = "pending"  # pending, succeeded, failed, refunded
    payment_method: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore."""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at
        return data

    @classmethod
    def from_dict(cls, doc_id: str, data: Dict[str, Any]) -> 'PaymentRecord':
        """Create PaymentRecord from Firestore document."""
        return cls(
            id=doc_id,
            user_uid=data.get('user_uid', ''),
            subscription_id=data.get('subscription_id'),
            stripe_payment_intent_id=data.get('stripe_payment_intent_id', ''),
            stripe_charge_id=data.get('stripe_charge_id'),
            amount=data.get('amount', 0),
            currency=data.get('currency', 'usd'),
            status=data.get('status', 'pending'),
            payment_method=data.get('payment_method'),
            created_at=data.get('created_at'),
            metadata=data.get('metadata', {})
        )


class FirebaseManager:
    """Firebase manager for SousSpeed application."""
    
    def __init__(self):
        """Initialize Firebase app and Firestore client."""
        self.initialize_firebase()
        self.db = firestore.client()
    
    def initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        if not firebase_admin._apps:
            # Check for service account key file
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY', 'firebase-service-account.json')
            
            if os.path.exists(service_account_path):
                # Use service account file
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            else:
                # Use environment variable with service account JSON
                service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
                if service_account_json:
                    service_account_info = json.loads(service_account_json)
                    cred = credentials.Certificate(service_account_info)
                    firebase_admin.initialize_app(cred)
                else:
                    # Use default credentials (for Google Cloud environments)
                    firebase_admin.initialize_app()
    
    # User Management Methods
    def create_firebase_user(self, email: str, password: str, name: str) -> Optional[str]:
        """Create user in Firebase Authentication."""
        try:
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=name,
                email_verified=False
            )
            return user_record.uid
        except auth.EmailAlreadyExistsError:
            return None
        except Exception as e:
            print(f"Error creating Firebase user: {e}")
            return None
    
    def verify_firebase_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return decoded claims."""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Error verifying Firebase token: {e}")
            return None
    
    def get_firebase_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get Firebase user by UID."""
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'creation_timestamp': user_record.user_metadata.creation_timestamp,
                'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp
            }
        except Exception as e:
            print(f"Error getting Firebase user: {e}")
            return None
    
    def create_user_profile(self, uid: str, user_data: Dict[str, Any]) -> bool:
        """Create user profile in Firestore."""
        try:
            user_ref = self.db.collection('users').document(uid)
            user_data['created_at'] = firestore.SERVER_TIMESTAMP
            user_data['updated_at'] = firestore.SERVER_TIMESTAMP
            user_ref.set(user_data)
            
            # Create initial free subscription
            self.create_subscription(uid, PlanType.FREE.value)
            return True
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    def get_user_profile(self, uid: str) -> Optional[User]:
        """Get user profile from Firestore."""
        try:
            user_ref = self.db.collection('users').document(uid)
            doc = user_ref.get()
            
            if doc.exists:
                return User.from_dict(uid, doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, uid: str, update_data: Dict[str, Any]) -> bool:
        """Update user profile in Firestore."""
        try:
            user_ref = self.db.collection('users').document(uid)
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            user_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def update_last_login(self, uid: str) -> bool:
        """Update user's last login timestamp."""
        return self.update_user_profile(uid, {'last_login': firestore.SERVER_TIMESTAMP})
    
    # Subscription Management Methods
    def create_subscription(self, user_uid: str, plan_type: str, 
                          stripe_customer_id: str = None,
                          stripe_subscription_id: str = None,
                          is_trial: bool = False) -> Optional[Subscription]:
        """Create a new subscription in Firestore."""
        try:
            now = datetime.now()
            
            # Deactivate existing subscriptions
            self.deactivate_user_subscriptions(user_uid)
            
            subscription_data = {
                'user_uid': user_uid,
                'plan_type': plan_type,
                'stripe_customer_id': stripe_customer_id,
                'stripe_subscription_id': stripe_subscription_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'metadata': {}
            }
            
            if is_trial:
                subscription_data.update({
                    'status': SubscriptionStatus.TRIAL.value,
                    'trial_start': now,
                    'trial_end': now + timedelta(days=7)
                })
            else:
                subscription_data.update({
                    'status': SubscriptionStatus.ACTIVE.value,
                    'period_start': now,
                    'period_end': now + timedelta(days=365)  # 1 year
                })
            
            # Add to Firestore
            doc_ref = self.db.collection('subscriptions').add(subscription_data)
            subscription_id = doc_ref[1].id
            
            return self.get_subscription_by_id(subscription_id)
        except Exception as e:
            print(f"Error creating subscription: {e}")
            return None
    
    def get_user_subscription(self, user_uid: str) -> Optional[Subscription]:
        """Get user's active subscription."""
        try:
            subscriptions_ref = self.db.collection('subscriptions')
            query = subscriptions_ref.where('user_uid', '==', user_uid)\
                                   .where('status', 'in', [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value])\
                                   .order_by('created_at', direction=firestore.Query.DESCENDING)\
                                   .limit(1)
            
            docs = query.get()
            if docs:
                doc = docs[0]
                return Subscription.from_dict(doc.id, doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting user subscription: {e}")
            return None
    
    def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by document ID."""
        try:
            doc_ref = self.db.collection('subscriptions').document(subscription_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return Subscription.from_dict(doc.id, doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting subscription by ID: {e}")
            return None
    
    def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID."""
        try:
            subscriptions_ref = self.db.collection('subscriptions')
            query = subscriptions_ref.where('stripe_subscription_id', '==', stripe_subscription_id)
            docs = query.get()
            
            if docs:
                doc = docs[0]
                return Subscription.from_dict(doc.id, doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting subscription by Stripe ID: {e}")
            return None
    
    def update_subscription_status(self, subscription_id: str, status: str,
                                 metadata: Dict[str, Any] = None) -> bool:
        """Update subscription status in Firestore."""
        try:
            doc_ref = self.db.collection('subscriptions').document(subscription_id)
            
            update_data = {
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            if metadata:
                update_data['metadata'] = metadata
            
            if status == SubscriptionStatus.CANCELLED.value:
                update_data['cancelled_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating subscription status: {e}")
            return False
    
    def deactivate_user_subscriptions(self, user_uid: str) -> bool:
        """Deactivate all active subscriptions for user."""
        try:
            subscriptions_ref = self.db.collection('subscriptions')
            query = subscriptions_ref.where('user_uid', '==', user_uid)\
                                   .where('status', 'in', [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value])
            
            docs = query.get()
            batch = self.db.batch()
            
            for doc in docs:
                batch.update(doc.reference, {
                    'status': SubscriptionStatus.EXPIRED.value,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
            
            batch.commit()
            return True
        except Exception as e:
            print(f"Error deactivating subscriptions: {e}")
            return False
    
    # Payment Records Methods
    def create_payment_record(self, user_uid: str, subscription_id: str,
                            stripe_payment_intent_id: str, amount: int,
                            currency: str = "usd", status: str = "pending",
                            metadata: Dict[str, Any] = None) -> Optional[PaymentRecord]:
        """Create a payment record in Firestore."""
        try:
            payment_data = {
                'user_uid': user_uid,
                'subscription_id': subscription_id,
                'stripe_payment_intent_id': stripe_payment_intent_id,
                'amount': amount,
                'currency': currency,
                'status': status,
                'created_at': firestore.SERVER_TIMESTAMP,
                'metadata': metadata or {}
            }
            
            doc_ref = self.db.collection('payment_records').add(payment_data)
            payment_id = doc_ref[1].id
            
            return self.get_payment_record_by_id(payment_id)
        except Exception as e:
            print(f"Error creating payment record: {e}")
            return None
    
    def get_payment_record_by_id(self, payment_id: str) -> Optional[PaymentRecord]:
        """Get payment record by document ID."""
        try:
            doc_ref = self.db.collection('payment_records').document(payment_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return PaymentRecord.from_dict(doc.id, doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting payment record: {e}")
            return None
    
    def get_payment_by_intent_id(self, stripe_payment_intent_id: str) -> Optional[PaymentRecord]:
        """Get payment record by Stripe payment intent ID."""
        try:
            payments_ref = self.db.collection('payment_records')
            query = payments_ref.where('stripe_payment_intent_id', '==', stripe_payment_intent_id)
            docs = query.get()
            
            if docs:
                doc = docs[0]
                return PaymentRecord.from_dict(doc.id, doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting payment by intent ID: {e}")
            return None
    
    def update_payment_status(self, payment_id: str, status: str,
                            stripe_charge_id: str = None,
                            payment_method: str = None,
                            metadata: Dict[str, Any] = None) -> bool:
        """Update payment record status."""
        try:
            doc_ref = self.db.collection('payment_records').document(payment_id)
            
            update_data = {'status': status}
            
            if stripe_charge_id:
                update_data['stripe_charge_id'] = stripe_charge_id
            
            if payment_method:
                update_data['payment_method'] = payment_method
            
            if metadata:
                update_data['metadata'] = metadata
            
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating payment status: {e}")
            return False
    
    # Utility Methods
    def check_user_access(self, user_uid: str, feature: str) -> bool:
        """Check if user has access to a specific feature."""
        try:
            subscription = self.get_user_subscription(user_uid)
            
            if not subscription:
                return feature == 'beef'  # Only beef for free users
            
            # Check if subscription is active or in trial
            if subscription.status not in [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value]:
                return feature == 'beef'
            
            # Check if trial has expired
            if subscription.status == SubscriptionStatus.TRIAL.value and subscription.trial_end:
                if datetime.now() > subscription.trial_end.replace(tzinfo=None):
                    # Update subscription status to expired
                    self.update_subscription_status(subscription.id, SubscriptionStatus.EXPIRED.value)
                    return feature == 'beef'
            
            # Check if paid subscription has expired
            if subscription.status == SubscriptionStatus.ACTIVE.value and subscription.period_end:
                if datetime.now() > subscription.period_end.replace(tzinfo=None):
                    # Update subscription status to expired
                    self.update_subscription_status(subscription.id, SubscriptionStatus.EXPIRED.value)
                    return feature == 'beef'
            
            # Free plan only allows beef
            if subscription.plan_type == PlanType.FREE.value:
                return feature == 'beef'
            
            # Pro plan allows everything
            if subscription.plan_type == PlanType.PRO_CHEF.value:
                return True
            
            return False
        except Exception as e:
            print(f"Error checking user access: {e}")
            return False
    
    def get_user_stats(self, user_uid: str) -> Dict[str, Any]:
        """Get user statistics and subscription info."""
        try:
            user = self.get_user_profile(user_uid)
            subscription = self.get_user_subscription(user_uid)
            
            if not user:
                return {}
            
            # Get payment statistics
            payments_ref = self.db.collection('payment_records')
            query = payments_ref.where('user_uid', '==', user_uid)\
                               .where('status', '==', 'succeeded')
            payments = query.get()
            
            total_paid = sum(doc.to_dict().get('amount', 0) for doc in payments)
            
            return {
                'user': {
                    'uid': user.uid,
                    'email': user.email,
                    'name': user.name,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'is_verified': user.is_verified
                },
                'subscription': {
                    'plan_type': subscription.plan_type if subscription else 'free',
                    'status': subscription.status if subscription else 'expired',
                    'trial_end': subscription.trial_end.isoformat() if subscription and subscription.trial_end else None,
                    'period_end': subscription.period_end.isoformat() if subscription and subscription.period_end else None,
                },
                'payments': {
                    'count': len(payments),
                    'total_paid_cents': total_paid,
                    'total_paid_dollars': total_paid / 100
                }
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {}


# Initialize Firebase manager instance
firebase_db = FirebaseManager()
