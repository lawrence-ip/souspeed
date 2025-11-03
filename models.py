#!/usr/bin/env python3
"""
Database models for SousSpeed user management and subscriptions.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sqlite3
import hashlib
import secrets
import json
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
    """User data model."""
    id: Optional[int] = None
    email: str = ""
    name: str = ""
    password_hash: str = ""
    salt: str = ""
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_verified: bool = False
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_expires: Optional[datetime] = None


@dataclass
class Subscription:
    """Subscription data model."""
    id: Optional[int] = None
    user_id: int = 0
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
    metadata: str = "{}"  # JSON string for additional data


@dataclass
class PaymentRecord:
    """Payment transaction record."""
    id: Optional[int] = None
    user_id: int = 0
    subscription_id: Optional[int] = None
    stripe_payment_intent_id: str = ""
    stripe_charge_id: Optional[str] = None
    amount: int = 0  # Amount in cents
    currency: str = "usd"
    status: str = "pending"  # pending, succeeded, failed, refunded
    payment_method: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: str = "{}"


class DatabaseManager:
    """Database manager for SousSpeed application."""
    
    def __init__(self, db_path: str = "souspeed.db"):
        """Initialize database manager."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_verified BOOLEAN DEFAULT FALSE,
                    verification_token TEXT,
                    reset_token TEXT,
                    reset_expires TIMESTAMP
                )
            """)
            
            # Subscriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_type TEXT NOT NULL DEFAULT 'free',
                    status TEXT NOT NULL DEFAULT 'expired',
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT UNIQUE,
                    stripe_payment_intent_id TEXT,
                    trial_start TIMESTAMP,
                    trial_end TIMESTAMP,
                    period_start TIMESTAMP,
                    period_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # Payment records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subscription_id INTEGER,
                    stripe_payment_intent_id TEXT NOT NULL,
                    stripe_charge_id TEXT,
                    amount INTEGER NOT NULL,
                    currency TEXT DEFAULT 'usd',
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe ON subscriptions (stripe_subscription_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_user ON payment_records (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_intent ON payment_records (stripe_payment_intent_id)")
            
            conn.commit()
    
    def get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # User Management Methods
    def create_user(self, email: str, name: str, password: str) -> Optional[User]:
        """Create a new user with hashed password."""
        try:
            # Generate salt and hash password
            salt = secrets.token_hex(32)
            password_hash = hashlib.pbkdf2_hmac('sha256', 
                                              password.encode('utf-8'),
                                              salt.encode('utf-8'),
                                              100000)  # 100k iterations
            
            verification_token = secrets.token_urlsafe(32)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (email, name, password_hash, salt, verification_token)
                    VALUES (?, ?, ?, ?, ?)
                """, (email, name, password_hash.hex(), salt, verification_token))
                
                user_id = cursor.lastrowid
                
                # Create initial free subscription
                cursor.execute("""
                    INSERT INTO subscriptions (user_id, plan_type, status)
                    VALUES (?, ?, ?)
                """, (user_id, PlanType.FREE.value, SubscriptionStatus.ACTIVE.value))
                
                conn.commit()
                
                return self.get_user_by_id(user_id)
        except sqlite3.IntegrityError:
            return None  # Email already exists
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        # Hash the provided password with the stored salt
        password_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          user.salt.encode('utf-8'),
                                          100000)
        
        if password_hash.hex() == user.password_hash:
            # Update last login
            self.update_last_login(user.id)
            return user
        
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    id=row['id'],
                    email=row['email'],
                    name=row['name'],
                    password_hash=row['password_hash'],
                    salt=row['salt'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                    is_verified=bool(row['is_verified']),
                    verification_token=row['verification_token'],
                    reset_token=row['reset_token'],
                    reset_expires=datetime.fromisoformat(row['reset_expires']) if row['reset_expires'] else None
                )
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    id=row['id'],
                    email=row['email'],
                    name=row['name'],
                    password_hash=row['password_hash'],
                    salt=row['salt'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                    is_verified=bool(row['is_verified']),
                    verification_token=row['verification_token'],
                    reset_token=row['reset_token'],
                    reset_expires=datetime.fromisoformat(row['reset_expires']) if row['reset_expires'] else None
                )
        return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            """, (user_id,))
            conn.commit()
    
    def verify_user(self, verification_token: str) -> bool:
        """Verify user email with token."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET is_verified = TRUE, verification_token = NULL
                WHERE verification_token = ?
            """, (verification_token,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Subscription Management Methods
    def create_subscription(self, user_id: int, plan_type: str, 
                          stripe_customer_id: str = None,
                          stripe_subscription_id: str = None,
                          is_trial: bool = False) -> Optional[Subscription]:
        """Create a new subscription."""
        try:
            now = datetime.now()
            
            if is_trial:
                status = SubscriptionStatus.TRIAL.value
                trial_start = now
                trial_end = now + timedelta(days=7)  # 7-day trial
                period_start = None
                period_end = None
            else:
                status = SubscriptionStatus.ACTIVE.value
                trial_start = None
                trial_end = None
                period_start = now
                period_end = now + timedelta(days=365)  # 1 year
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Deactivate any existing subscriptions
                cursor.execute("""
                    UPDATE subscriptions 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND status IN (?, ?)
                """, (SubscriptionStatus.EXPIRED.value, user_id, 
                     SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value))
                
                # Create new subscription
                cursor.execute("""
                    INSERT INTO subscriptions 
                    (user_id, plan_type, status, stripe_customer_id, stripe_subscription_id,
                     trial_start, trial_end, period_start, period_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, plan_type, status, stripe_customer_id, stripe_subscription_id,
                     trial_start, trial_end, period_start, period_end))
                
                subscription_id = cursor.lastrowid
                conn.commit()
                
                return self.get_subscription_by_id(subscription_id)
        except Exception as e:
            print(f"Error creating subscription: {e}")
            return None
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND status IN (?, ?)
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_subscription(row)
        return None
    
    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscriptions WHERE id = ?", (subscription_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_subscription(row)
        return None
    
    def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions WHERE stripe_subscription_id = ?
            """, (stripe_subscription_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_subscription(row)
        return None
    
    def update_subscription_status(self, subscription_id: int, status: str,
                                 metadata: Dict[str, Any] = None):
        """Update subscription status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            update_data = [status, subscription_id]
            query = "UPDATE subscriptions SET status = ?, updated_at = CURRENT_TIMESTAMP"
            
            if metadata:
                query += ", metadata = ?"
                update_data.insert(-1, json.dumps(metadata))
            
            if status == SubscriptionStatus.CANCELLED.value:
                query += ", cancelled_at = CURRENT_TIMESTAMP"
            
            query += " WHERE id = ?"
            
            cursor.execute(query, update_data)
            conn.commit()
    
    def _row_to_subscription(self, row) -> Subscription:
        """Convert database row to Subscription object."""
        return Subscription(
            id=row['id'],
            user_id=row['user_id'],
            plan_type=row['plan_type'],
            status=row['status'],
            stripe_customer_id=row['stripe_customer_id'],
            stripe_subscription_id=row['stripe_subscription_id'],
            stripe_payment_intent_id=row['stripe_payment_intent_id'],
            trial_start=datetime.fromisoformat(row['trial_start']) if row['trial_start'] else None,
            trial_end=datetime.fromisoformat(row['trial_end']) if row['trial_end'] else None,
            period_start=datetime.fromisoformat(row['period_start']) if row['period_start'] else None,
            period_end=datetime.fromisoformat(row['period_end']) if row['period_end'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
            metadata=row['metadata'] or "{}"
        )
    
    # Payment Records Methods
    def create_payment_record(self, user_id: int, subscription_id: int,
                            stripe_payment_intent_id: str, amount: int,
                            currency: str = "usd", status: str = "pending",
                            metadata: Dict[str, Any] = None) -> Optional[PaymentRecord]:
        """Create a payment record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO payment_records 
                    (user_id, subscription_id, stripe_payment_intent_id, amount, currency, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, subscription_id, stripe_payment_intent_id, amount, currency, status,
                     json.dumps(metadata or {})))
                
                payment_id = cursor.lastrowid
                conn.commit()
                
                return self.get_payment_record_by_id(payment_id)
        except Exception as e:
            print(f"Error creating payment record: {e}")
            return None
    
    def get_payment_record_by_id(self, payment_id: int) -> Optional[PaymentRecord]:
        """Get payment record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payment_records WHERE id = ?", (payment_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_payment_record(row)
        return None
    
    def get_payment_by_intent_id(self, stripe_payment_intent_id: str) -> Optional[PaymentRecord]:
        """Get payment record by Stripe payment intent ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM payment_records WHERE stripe_payment_intent_id = ?
            """, (stripe_payment_intent_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_payment_record(row)
        return None
    
    def update_payment_status(self, payment_id: int, status: str,
                            stripe_charge_id: str = None,
                            payment_method: str = None,
                            metadata: Dict[str, Any] = None):
        """Update payment record status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            update_fields = ["status = ?"]
            update_values = [status]
            
            if stripe_charge_id:
                update_fields.append("stripe_charge_id = ?")
                update_values.append(stripe_charge_id)
            
            if payment_method:
                update_fields.append("payment_method = ?")
                update_values.append(payment_method)
            
            if metadata:
                update_fields.append("metadata = ?")
                update_values.append(json.dumps(metadata))
            
            update_values.append(payment_id)
            
            query = f"UPDATE payment_records SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
            conn.commit()
    
    def _row_to_payment_record(self, row) -> PaymentRecord:
        """Convert database row to PaymentRecord object."""
        return PaymentRecord(
            id=row['id'],
            user_id=row['user_id'],
            subscription_id=row['subscription_id'],
            stripe_payment_intent_id=row['stripe_payment_intent_id'],
            stripe_charge_id=row['stripe_charge_id'],
            amount=row['amount'],
            currency=row['currency'],
            status=row['status'],
            payment_method=row['payment_method'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            metadata=row['metadata'] or "{}"
        )
    
    # Utility Methods
    def check_user_access(self, user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature."""
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return False
        
        # Check if subscription is active or in trial
        if subscription.status not in [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value]:
            return False
        
        # Check if trial has expired
        if subscription.status == SubscriptionStatus.TRIAL.value and subscription.trial_end:
            if datetime.now() > subscription.trial_end:
                # Update subscription status to expired
                self.update_subscription_status(subscription.id, SubscriptionStatus.EXPIRED.value)
                return False
        
        # Check if paid subscription has expired
        if subscription.status == SubscriptionStatus.ACTIVE.value and subscription.period_end:
            if datetime.now() > subscription.period_end:
                # Update subscription status to expired
                self.update_subscription_status(subscription.id, SubscriptionStatus.EXPIRED.value)
                return False
        
        # Free plan only allows beef
        if subscription.plan_type == PlanType.FREE.value:
            return feature == 'beef'
        
        # Pro plan allows everything
        if subscription.plan_type == PlanType.PRO_CHEF.value:
            return True
        
        return False
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics and subscription info."""
        user = self.get_user_by_id(user_id)
        subscription = self.get_user_subscription(user_id)
        
        if not user:
            return {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get payment history
            cursor.execute("""
                SELECT COUNT(*) as payment_count, SUM(amount) as total_paid
                FROM payment_records 
                WHERE user_id = ? AND status = 'succeeded'
            """, (user_id,))
            payment_stats = cursor.fetchone()
        
        return {
            'user': {
                'id': user.id,
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
                'count': payment_stats['payment_count'] or 0,
                'total_paid_cents': payment_stats['total_paid'] or 0,
                'total_paid_dollars': (payment_stats['total_paid'] or 0) / 100
            }
        }


# Initialize database manager instance
db = DatabaseManager()
