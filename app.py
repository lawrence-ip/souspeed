#!/usr/bin/env python3
"""
Production Flask application for SousSpeed deployment on Digital Ocean.
Serves both static files and API endpoints.
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string, send_file, session
from flask_cors import CORS
import json
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from thermo_calculator import ThermodynamicCalculator
from firebase_models import FirebaseManager, User, PlanType
from stripe_integration import StripePaymentManager
from firebase_config import get_firebase_config

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, supports_credentials=True)

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

# Initialize services
calculator = ThermodynamicCalculator()
db = FirebaseManager()
payment_manager = StripePaymentManager(db)

@app.route('/')
def index():
    """Serve the main HTML page."""
    try:
        with open('index.html', 'r') as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return """
        <h1>SousSpeed - Sous Vide Optimization Tool</h1>
        <p>Welcome to SousSpeed! The advanced thermodynamic calculator for sous vide cooking.</p>
        <p>API is running at <a href="/api/health">/api/health</a></p>
        """, 200

@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serve static files (CSS, JS, images, etc.)."""
    try:
        # Handle specific file types
        if filename.endswith('.css'):
            return send_from_directory('.', filename, mimetype='text/css')
        elif filename.endswith('.js'):
            return send_from_directory('.', filename, mimetype='application/javascript')
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico')):
            return send_from_directory('.', filename)
        else:
            # For other files, let Flask handle it normally
            return send_from_directory('.', filename)
    except FileNotFoundError:
        return "File not found", 404

@app.route('/api/calculate', methods=['POST'])
def calculate_cooking_parameters():
    """Calculate optimal sous vide cooking parameters with access control."""
    try:
        data = request.get_json()
        
        protein_type = data.get('protein_type', 'beef')
        thickness_inches = float(data.get('thickness_inches', 1.0))
        target_temp_celsius = float(data.get('target_temp_celsius', 54.0))
        doneness = data.get('doneness', 'medium-rare')
        weight_kg = data.get('weight_kg')
        
        if weight_kg is not None:
            weight_kg = float(weight_kg)
        
        # Validate inputs
        if thickness_inches <= 0 or thickness_inches > 10:
            return jsonify({'error': 'Thickness must be between 0.1 and 10 inches'}), 400
        
        if target_temp_celsius < 40 or target_temp_celsius > 100:
            return jsonify({'error': 'Temperature must be between 40°C and 100°C'}), 400
        
        if protein_type not in ['beef', 'chicken', 'pork', 'fish', 'vegetables']:
            return jsonify({'error': 'Invalid protein type'}), 400
        
        # Check user access for premium proteins
        current_user = get_current_user()
        if protein_type != 'beef':  # Beef is always free
            if not current_user:
                return jsonify({
                    'error': 'Authentication required for premium proteins',
                    'requires_upgrade': True,
                    'protein_type': protein_type
                }), 401
            
            # Check if user has access to this protein type
            if not db.check_user_access(current_user.id, protein_type):
                subscription_status = payment_manager.get_subscription_status(current_user.id)
                return jsonify({
                    'error': f'Pro Chef subscription required for {protein_type} calculations',
                    'requires_upgrade': True,
                    'protein_type': protein_type,
                    'current_plan': subscription_status.get('plan_type', 'free'),
                    'subscription_status': subscription_status
                }), 403
        
        # Calculate parameters
        result = calculator.calculate_cooking_parameters(
            protein_type=protein_type,
            thickness_inches=thickness_inches,
            target_temp_celsius=target_temp_celsius,
            doneness=doneness,
            weight_kg=weight_kg
        )
        
        # Add user subscription info to response if authenticated
        if current_user:
            subscription_status = payment_manager.get_subscription_status(current_user.id)
            result['user_subscription'] = subscription_status
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Calculation failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'souspeed-api',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'database': 'connected',
        'stripe': 'configured'
    })

# Authentication helpers for Firebase
def verify_firebase_token(token: str) -> dict:
    """Verify Firebase ID token and return decoded claims."""
    return db.verify_firebase_token(token)

def require_auth(f):
    """Decorator to require Firebase authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix
            decoded_token = verify_firebase_token(token)
            if decoded_token:
                request.user_uid = decoded_token['uid']
                request.user_email = decoded_token.get('email')
                return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required'}), 401
    return decorated_function

def get_current_user():
    """Get current user from request context."""
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
        decoded_token = verify_firebase_token(token)
        if decoded_token:
            return db.get_user_profile(decoded_token['uid'])
    return None

# Authentication endpoints
@app.route('/api/auth/verify-token', methods=['POST'])
def verify_token():
    """Verify Firebase ID token and create/update user profile."""
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        # Verify Firebase token
        decoded_token = db.verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name') or decoded_token.get('display_name', '')
        
        # Get or create user profile
        user_profile = db.get_user_profile(uid)
        
        if not user_profile:
            # Create new user profile
            user_data = {
                'email': email,
                'name': name,
                'is_verified': decoded_token.get('email_verified', False)
            }
            
            if db.create_user_profile(uid, user_data):
                user_profile = db.get_user_profile(uid)
            else:
                return jsonify({'error': 'Failed to create user profile'}), 500
        else:
            # Update last login
            db.update_last_login(uid)
        
        # Get subscription status
        subscription_status = payment_manager.get_subscription_status(uid)
        
        return jsonify({
            'success': True,
            'message': 'Authentication successful',
            'user': {
                'uid': user_profile.uid,
                'email': user_profile.email,
                'name': user_profile.name,
                'created_at': user_profile.created_at.isoformat() if user_profile.created_at else None,
                'last_login': user_profile.last_login.isoformat() if user_profile.last_login else None,
                'is_verified': user_profile.is_verified
            },
            'subscription': subscription_status
        })
        
    except Exception as e:
        return jsonify({'error': f'Token verification failed: {str(e)}'}), 500

@app.route('/api/auth/firebase-config', methods=['GET'])
def get_firebase_client_config():
    """Get Firebase configuration for frontend initialization."""
    try:
        config = get_firebase_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get Firebase config: {str(e)}'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@firebase_token_required
def get_profile():
    """Get user profile and subscription status."""
    try:
        current_uid = get_current_user_uid()
        user_profile = db.get_user_profile(current_uid)
        
        if not user_profile:
            return jsonify({'error': 'User profile not found'}), 404
        
        # Get subscription status
        subscription_status = payment_manager.get_subscription_status(current_uid)
        
        return jsonify({
            'success': True,
            'user': {
                'uid': user_profile.uid,
                'email': user_profile.email,
                'name': user_profile.name,
                'created_at': user_profile.created_at.isoformat() if user_profile.created_at else None,
                'last_login': user_profile.last_login.isoformat() if user_profile.last_login else None,
                'is_verified': user_profile.is_verified
            },
            'subscription': subscription_status
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

# Payment endpoints
@app.route('/api/payment/create-checkout', methods=['POST'])
@firebase_token_required
def create_checkout_session():
    """Create Stripe checkout session for subscription."""
    try:
        data = request.get_json()
        plan_type = data.get('plan_type', 'pro_chef')
        trial_days = data.get('trial_days', 7)
        
        # Get base URL for redirects
        base_url = request.host_url.rstrip('/')
        success_url = f"{base_url}/payment-success"
        cancel_url = f"{base_url}/payment-cancelled"
        
        current_uid = get_current_user_uid()
        
        # Create checkout session
        result = payment_manager.create_checkout_session(
            user_id=current_uid,
            plan_type=plan_type,
            success_url=success_url,
            cancel_url=cancel_url,
            trial_days=trial_days
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to create checkout: {str(e)}'}), 500

@app.route('/api/payment/create-intent', methods=['POST'])
@require_auth
def create_payment_intent():
    """Create payment intent for one-time payments."""
    try:
        data = request.get_json()
        amount = data.get('amount', 1000)  # Default $10.00 in cents
        currency = data.get('currency', 'usd')
        
        result = payment_manager.create_payment_intent(
            user_id=request.user_id,
            amount=amount,
            currency=currency,
            metadata={'plan_type': 'pro_chef'}
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to create payment intent: {str(e)}'}), 500

@app.route('/api/payment/success', methods=['POST'])
@require_auth
def payment_success():
    """Handle successful payment confirmation."""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({'error': 'Payment intent ID required'}), 400
        
        result = payment_manager.handle_successful_payment(payment_intent_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to process payment success: {str(e)}'}), 500

@app.route('/api/subscription/status', methods=['GET'])
@firebase_token_required
def subscription_status():
    """Get current subscription status."""
    try:
        current_uid = get_current_user_uid()
        status = payment_manager.get_subscription_status(current_uid)
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get subscription status: {str(e)}'}), 500

@app.route('/api/subscription/cancel', methods=['POST'])
@firebase_token_required
def cancel_subscription():
    """Cancel user subscription."""
    try:
        data = request.get_json()
        immediately = data.get('immediately', False)
        
        current_uid = get_current_user_uid()
        result = payment_manager.cancel_subscription(current_uid, immediately)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Failed to cancel subscription: {str(e)}'}), 500

# Stripe webhook endpoint
@app.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    try:
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            return jsonify({'error': 'Missing Stripe signature'}), 400
        
        result = payment_manager.handle_webhook(payload, sig_header)
        
        if 'error' in result:
            print(f"Webhook error: {result['error']}")
            return jsonify(result), 400
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@app.route('/api/protein-properties', methods=['GET'])
def get_protein_properties():
    """Get thermal properties for all proteins."""
    properties = {}
    for protein, props in calculator.protein_properties.items():
        properties[protein] = {
            'density': props.density,
            'specific_heat': props.specific_heat,
            'thermal_conductivity': props.thermal_conductivity,
            'thermal_diffusivity': props.thermal_diffusivity
        }
    return jsonify(properties)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Production configuration - flexible port handling
    port = int(os.environ.get('PORT', os.environ.get('HTTP_PORT', 8080)))
    debug = os.environ.get('FLASK_ENV') == 'development'
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🚀 Starting SousSpeed Production Server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print("   Available endpoints:")
    print("     GET  / - Main application")
    print("     POST /api/calculate - Calculate cooking parameters")
    print("     GET  /api/health - Health check")
    print("     GET  /api/protein-properties - Protein properties")
    
    app.run(host=host, port=port, debug=debug)
