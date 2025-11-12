#!/usr/bin/env python3
"""
One-time script to get OAuth2 refresh token for Vertex AI access.

This script will:
1. Open your browser for Google OAuth consent
2. You'll log in and grant permissions
3. Get a refresh token that never expires
4. Display the token for you to add to Railway

Run this once, then delete it (or keep for future use).
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

# OAuth2 credentials from GCP Console
CLIENT_ID = "YOUR_GCP_CLIENT_ID.apps.googleusercontent.com"
CLIENT_SECRET = "YOUR_GCP_CLIENT_SECRET"

# Scopes needed for Vertex AI (Imagen 3 + Veo)
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',  # Full Vertex AI access
]

def get_refresh_token():
    """Run OAuth flow and get refresh token."""

    print("\n" + "="*60)
    print("🔐 ORLA3 OAuth2 Token Generator")
    print("="*60)
    print("\nThis script will:")
    print("1. Open your browser")
    print("2. Ask you to log in to Google")
    print("3. Request permission to access Vertex AI")
    print("4. Give you a REFRESH TOKEN to store in Railway\n")

    # Create client config
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"]
        }
    }

    try:
        # Run OAuth flow
        flow = InstalledAppFlow.from_client_config(
            client_config,
            scopes=SCOPES
        )

        print("🌐 Opening browser for authentication...")
        print("👉 If browser doesn't open, copy the URL from terminal\n")

        # This will open browser and wait for user consent
        credentials = flow.run_local_server(
            port=8080,
            prompt='consent',
            success_message='✅ Authentication successful! You can close this window and return to terminal.'
        )

        print("\n" + "="*60)
        print("✅ SUCCESS! Authentication complete!")
        print("="*60)

        # Display the tokens
        print("\n📋 YOUR CREDENTIALS (add these to Railway):\n")

        print("1️⃣  GCP_CLIENT_ID")
        print(f"   {CLIENT_ID}\n")

        print("2️⃣  GCP_CLIENT_SECRET")
        print(f"   {CLIENT_SECRET}\n")

        print("3️⃣  GCP_REFRESH_TOKEN")
        print(f"   {credentials.refresh_token}\n")

        print("4️⃣  GCP_PROJECT_ID")
        print(f"   gen-lang-client-0902837589\n")

        print("="*60)
        print("📝 NEXT STEPS:")
        print("="*60)
        print("1. Go to Railway → Your Backend Service → Variables")
        print("2. Add these 4 variables (copy from above)")
        print("3. Railway will auto-deploy")
        print("4. Test Imagen 3 on marketing.orla3.com")
        print("="*60)

        # Save to file for backup
        token_data = {
            "GCP_CLIENT_ID": CLIENT_ID,
            "GCP_CLIENT_SECRET": CLIENT_SECRET,
            "GCP_REFRESH_TOKEN": credentials.refresh_token,
            "GCP_PROJECT_ID": "gen-lang-client-0902837589"
        }

        with open("oauth_tokens.json", "w") as f:
            json.dump(token_data, f, indent=2)

        print("\n💾 Tokens also saved to: oauth_tokens.json")
        print("⚠️  Keep this file PRIVATE (it's in .gitignore)\n")

        return credentials.refresh_token

    except Exception as e:
        print(f"\n❌ Error during authentication: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you created OAuth consent screen")
        print("2. Check that OAuth client is 'Desktop app' type")
        print("3. Try running script again")
        return None

if __name__ == "__main__":
    refresh_token = get_refresh_token()

    if refresh_token:
        print("\n✅ All done! Add the tokens to Railway and you're set!\n")
    else:
        print("\n❌ Failed to get refresh token. Please try again.\n")
