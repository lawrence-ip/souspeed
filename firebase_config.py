"""Firebase configuration for SousSpeed application."""

import os
import json

# Firebase project configuration
FIREBASE_CONFIG = {
    "apiKey": os.getenv('FIREBASE_API_KEY'),
    "authDomain": f"{os.getenv('FIREBASE_PROJECT_ID', 'souspeed-app')}.firebaseapp.com",
    "projectId": os.getenv('FIREBASE_PROJECT_ID', 'souspeed-app'),
    "storageBucket": f"{os.getenv('FIREBASE_PROJECT_ID', 'souspeed-app')}.appspot.com",
    "messagingSenderId": os.getenv('FIREBASE_SENDER_ID'),
    "appId": os.getenv('FIREBASE_APP_ID'),
    "databaseURL": f"https://{os.getenv('FIREBASE_PROJECT_ID', 'souspeed-app')}-default-rtdb.firebaseio.com/"
}

# Path to Firebase service account credentials
SERVICE_ACCOUNT_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'serviceAccountKey.json')

def get_firebase_config():
    """Get Firebase configuration for frontend."""
    return {
        "apiKey": FIREBASE_CONFIG["apiKey"],
        "authDomain": FIREBASE_CONFIG["authDomain"],
        "projectId": FIREBASE_CONFIG["projectId"],
        "storageBucket": FIREBASE_CONFIG["storageBucket"],
        "messagingSenderId": FIREBASE_CONFIG["messagingSenderId"],
        "appId": FIREBASE_CONFIG["appId"]
    }

def validate_firebase_config():
    """Validate that all required Firebase configuration is present."""
    required_keys = ['apiKey', 'projectId', 'messagingSenderId', 'appId']
    missing_keys = []
    
    for key in required_keys:
        if not FIREBASE_CONFIG.get(key):
            missing_keys.append(key)
    
    if missing_keys:
        raise ValueError(f"Missing Firebase configuration: {', '.join(missing_keys)}")
    
    # Check if service account file exists
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        raise FileNotFoundError(f"Firebase service account file not found: {SERVICE_ACCOUNT_PATH}")
    
    return True
