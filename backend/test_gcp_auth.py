#!/usr/bin/env python3
"""
Test GCP OAuth2 authentication
"""
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

load_dotenv()

GCP_CLIENT_ID = os.getenv("GCP_CLIENT_ID")
GCP_CLIENT_SECRET = os.getenv("GCP_CLIENT_SECRET")
GCP_REFRESH_TOKEN = os.getenv("GCP_REFRESH_TOKEN")

print(f"GCP_CLIENT_ID: {'✓ Present' if GCP_CLIENT_ID else '✗ Missing'}")
print(f"GCP_CLIENT_SECRET: {'✓ Present' if GCP_CLIENT_SECRET else '✗ Missing'}")
print(f"GCP_REFRESH_TOKEN: {'✓ Present' if GCP_REFRESH_TOKEN else '✗ Missing'}")

if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
    print("\n❌ Missing GCP credentials in .env file")
    exit(1)

print("\nTesting OAuth2 token refresh...")

try:
    credentials = Credentials(
        token=None,
        refresh_token=GCP_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GCP_CLIENT_ID,
        client_secret=GCP_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )

    credentials.refresh(GoogleAuthRequest())

    print(f"✅ Got fresh access token!")
    print(f"   Token: {credentials.token[:50]}...")
    print(f"   Expiry: {credentials.expiry}")

except Exception as e:
    print(f"❌ Failed to get access token: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
