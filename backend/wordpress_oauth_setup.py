#!/usr/bin/env python3
"""
WordPress.com OAuth Setup Helper
Generates OAuth token for publishing to WordPress.com blogs
"""

import os
import webbrowser
from urllib.parse import urlencode, parse_qs

# WordPress.com OAuth Application
# You need to create an app at: https://developer.wordpress.com/apps/
CLIENT_ID = os.getenv("WORDPRESS_CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.getenv("WORDPRESS_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/wordpress/callback"

def get_authorization_url():
    """Generate WordPress.com OAuth authorization URL"""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "posts"  # Request permission to create posts
    }

    auth_url = f"https://public-api.wordpress.com/oauth2/authorize?{urlencode(params)}"
    return auth_url

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    import httpx

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = httpx.post(
        "https://public-api.wordpress.com/oauth2/token",
        data=data
    )

    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def main():
    print("=" * 60)
    print("WordPress.com OAuth Setup")
    print("=" * 60)
    print()

    # Step 1: Check if app is configured
    if CLIENT_ID == "YOUR_CLIENT_ID" or CLIENT_SECRET == "YOUR_CLIENT_SECRET":
        print("⚠️  WordPress.com OAuth app not configured!")
        print()
        print("To set up WordPress.com publishing:")
        print()
        print("1. Go to: https://developer.wordpress.com/apps/")
        print("2. Click 'Create New Application'")
        print("3. Fill in:")
        print("   - Name: ORLA3 Marketing Suite")
        print("   - Description: Social media publishing tool")
        print("   - Website URL: https://marketing.orla3.com")
        print("   - Redirect URL: http://localhost:8000/wordpress/callback")
        print("   - Type: Web")
        print()
        print("4. Copy Client ID and Client Secret")
        print("5. Add to backend/.env:")
        print("   WORDPRESS_CLIENT_ID=your_client_id")
        print("   WORDPRESS_CLIENT_SECRET=your_client_secret")
        print("   WORDPRESS_SITE_ID=sgillespiea7d7336966-wgdcj.wordpress.com")
        print()
        print("6. Run this script again")
        return

    # Step 2: Generate authorization URL
    auth_url = get_authorization_url()
    print("Step 1: Authorize the app")
    print()
    print("Opening browser to authorize WordPress.com access...")
    print(f"URL: {auth_url}")
    print()

    # Open browser
    webbrowser.open(auth_url)

    print("After authorizing, you'll be redirected to:")
    print(f"{REDIRECT_URI}?code=AUTHORIZATION_CODE")
    print()
    print("Copy the 'code' parameter from the URL and paste it here:")
    code = input("Authorization Code: ").strip()

    if not code:
        print("❌ No code provided. Exiting.")
        return

    # Step 3: Exchange code for token
    print()
    print("Exchanging code for access token...")
    access_token = exchange_code_for_token(code)

    if access_token:
        print()
        print("✅ Success! Add this to your backend/.env:")
        print()
        print(f"WORDPRESS_ACCESS_TOKEN={access_token}")
        print("WORDPRESS_SITE_ID=sgillespiea7d7336966-wgdcj.wordpress.com")
        print()
        print("Then restart your backend server to use WordPress publishing!")
    else:
        print()
        print("❌ Failed to get access token. Check your credentials.")

if __name__ == "__main__":
    main()
