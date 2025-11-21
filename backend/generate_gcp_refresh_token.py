#!/usr/bin/env python3
"""
Generate a new GCP OAuth2 Refresh Token

This script will:
1. Open a browser for Google authentication
2. Get your authorization
3. Generate a new refresh token
4. Display it for you to copy to Railway

Requirements:
    pip install google-auth-oauthlib google-auth-httplib2
"""

import os
import sys

print("=" * 70)
print("🔐 GCP OAuth2 Refresh Token Generator")
print("=" * 70)
print()

# Check if required packages are installed
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("❌ Missing required packages!")
    print()
    print("Please install them:")
    print("  pip install google-auth-oauthlib google-auth-httplib2")
    print()
    sys.exit(1)

# Get credentials from environment or prompt
GCP_CLIENT_ID = os.getenv("GCP_CLIENT_ID")
GCP_CLIENT_SECRET = os.getenv("GCP_CLIENT_SECRET")

if not GCP_CLIENT_ID or not GCP_CLIENT_SECRET:
    print("⚠️  GCP_CLIENT_ID and GCP_CLIENT_SECRET not found in environment")
    print()
    print("Please enter them manually:")
    print()
    GCP_CLIENT_ID = input("GCP_CLIENT_ID: ").strip()
    GCP_CLIENT_SECRET = input("GCP_CLIENT_SECRET: ").strip()
    print()

if not GCP_CLIENT_ID or not GCP_CLIENT_SECRET:
    print("❌ Client ID and Secret are required!")
    sys.exit(1)

print(f"✅ Client ID: {GCP_CLIENT_ID[:20]}...")
print(f"✅ Client Secret: {GCP_CLIENT_SECRET[:20]}...")
print()

# Create client config
client_config = {
    "installed": {
        "client_id": GCP_CLIENT_ID,
        "client_secret": GCP_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"]
    }
}

# Scopes needed for Vertex AI (Imagen & Veo)
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

print("🌐 Starting OAuth2 flow...")
print()
print("This will:")
print("  1. Open your default browser")
print("  2. Ask you to sign in with your Google account")
print("  3. Grant permission to access Vertex AI")
print("  4. Generate a new refresh token")
print()

try:
    # Create the flow
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=SCOPES
    )

    # Run the OAuth flow
    print("🔓 Opening browser for authentication...")
    credentials = flow.run_local_server(
        port=8080,
        prompt='consent',  # Force consent screen to get refresh token
        success_message='✅ Authentication successful! You can close this window.',
        open_browser=True
    )

    if not credentials.refresh_token:
        print()
        print("❌ No refresh token received!")
        print()
        print("This can happen if you've already authorized this app.")
        print("To fix this:")
        print("  1. Go to https://myaccount.google.com/permissions")
        print("  2. Remove 'ORLA³ Marketing Suite' or your app name")
        print("  3. Run this script again")
        sys.exit(1)

    print()
    print("=" * 70)
    print("✅ SUCCESS! New Refresh Token Generated")
    print("=" * 70)
    print()
    print("Your new GCP_REFRESH_TOKEN:")
    print()
    print("-" * 70)
    print(credentials.refresh_token)
    print("-" * 70)
    print()
    print("📋 Next Steps:")
    print()
    print("1. Copy the token above")
    print("2. Go to Railway Dashboard → Your Service → Variables")
    print("3. Update GCP_REFRESH_TOKEN with the new token")
    print("4. Railway will automatically redeploy")
    print("5. Wait ~2 minutes and test AI generation")
    print()
    print("💡 Save this token securely - you won't see it again!")
    print()

except Exception as e:
    print()
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
