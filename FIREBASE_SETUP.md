# SousSpeed Firebase Setup Guide

## Firebase Configuration

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project named "souspeed-app" (or your preferred name)
3. Enable Authentication and Firestore Database

### 2. Configure Authentication

1. In Firebase Console, go to Authentication > Sign-in method
2. Enable Email/Password authentication
3. Optionally enable other providers (Google, etc.)

### 3. Configure Firestore Database

1. Go to Firestore Database
2. Create database in production mode
3. Set up security rules (start with test mode for development)

### 4. Get Firebase Configuration

1. Go to Project Settings > General
2. Scroll down to "Your apps" section
3. Add a web app if not already created
4. Copy the Firebase configuration object

### 5. Set Environment Variables

Create a `.env` file in your project root with:

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-api-key
FIREBASE_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id
```

### 6. Service Account Setup

1. Go to Project Settings > Service Accounts
2. Generate new private key
3. Save the JSON file as `serviceAccountKey.json` in your project root
4. Add this file to `.gitignore` for security

### 7. Firestore Security Rules

In Firestore Database > Rules, use these starter rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own profile
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Subscriptions readable by user, writable by server
    match /subscriptions/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if false; // Only server can write via admin SDK
    }
    
    // Payment records readable by user, writable by server
    match /payment_records/{recordId} {
      allow read: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
      allow write: if false; // Only server can write via admin SDK
    }
  }
}
```

### 8. Running the Application

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set the service account path environment variable:
   ```bash
   export FIREBASE_SERVICE_ACCOUNT_PATH=./serviceAccountKey.json
   ```

3. Run the Flask application:
   ```bash
   python app.py
   ```

### 9. Testing Authentication

- Visit the application in your browser
- Try creating a new account with email/password
- Test login functionality
- Check Firestore console to see user profiles being created
- Test password reset functionality

### Security Notes

- Keep `serviceAccountKey.json` secure and never commit to version control
- Use environment variables for all sensitive configuration
- Update Firestore security rules for production use
- Consider enabling Firebase App Check for additional security

### Troubleshooting

- Check browser console for Firebase initialization errors
- Verify environment variables are set correctly
- Ensure Firestore database exists and has proper rules
- Check that Authentication is enabled with Email/Password provider
- Verify service account key file exists and is valid JSON

## Production Deployment

For production deployment on Digital Ocean or other platforms:

1. Set environment variables in your hosting platform
2. Upload service account key securely (not in code repository)  
3. Update Firestore security rules for production
4. Enable Firebase App Check
5. Configure proper CORS settings
6. Set up monitoring and logging
