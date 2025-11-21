# Generate New GCP Refresh Token

## Quick Start

```bash
cd backend
pip install google-auth-oauthlib google-auth-httplib2
python3 generate_gcp_refresh_token.py
```

## What This Does

1. Opens your browser for Google authentication
2. You sign in with your Google account
3. Grant permission to access Vertex AI
4. Generates a new refresh token
5. Displays the token for you to copy

## Update Railway

After getting the new token:

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Select your service
3. Go to **Variables** tab
4. Find `GCP_REFRESH_TOKEN`
5. Click to edit
6. Paste the new token
7. Save (Railway will auto-redeploy)

## If You Get "No refresh token received"

This means you've already authorized the app before. To fix:

1. Go to https://myaccount.google.com/permissions
2. Find "ORLA³ Marketing Suite" (or your app name)
3. Click **Remove access**
4. Run the script again

## Testing After Update

Wait ~2 minutes for Railway to deploy, then test:

```bash
curl https://orla3-marketing-suite-app-production.up.railway.app/ai/test-gcp-auth
```

Should return:
```json
{
  "success": true,
  "message": "GCP OAuth2 authentication successful"
}
```

## Why Did This Happen?

Google OAuth refresh tokens can expire if:
- Not used for 6+ months
- OAuth consent screen was modified
- Google revoked it for security
- Client credentials were regenerated

The refresh token needs to be regenerated periodically.
