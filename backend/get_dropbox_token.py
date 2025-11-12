"""
Dropbox OAuth2 Token Generator
Generates a refresh token for Dropbox API access
"""
import webbrowser
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# Your Dropbox app credentials
APP_KEY = "YOUR_DROPBOX_APP_KEY"
APP_SECRET = "YOUR_DROPBOX_APP_SECRET"
REDIRECT_URI = "http://localhost:8080"

# Dropbox OAuth endpoints
AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"

# Global variable to store the authorization code
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code

        # Parse the authorization code from the callback
        query = parse_qs(self.path.split('?')[1] if '?' in self.path else '')

        if 'code' in query:
            auth_code = query['code'][0]

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """.encode())
        else:
            # Error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error = query.get('error', ['Unknown error'])[0]
            self.wfile.write(f"""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Authorization Failed</h1>
                    <p>Error: {error}</p>
                </body>
                </html>
            """.encode())

    def log_message(self, format, *args):
        # Suppress server logs
        pass

def get_authorization_code():
    """Step 1: Get authorization code"""
    print("\n🔐 Dropbox OAuth2 Token Generator")
    print("=" * 50)

    # Build authorization URL
    params = {
        'client_id': APP_KEY,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'token_access_type': 'offline'  # Request refresh token
    }

    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print("\n📋 Step 1: Authorize the application")
    print("Opening browser for authorization...")
    print("\nIf browser doesn't open, visit this URL:")
    print(f"\n{auth_url}\n")

    # Open browser
    webbrowser.open(auth_url)

    # Start local server to receive callback
    print("✅ Waiting for authorization callback...")
    print("(A browser window should open - please authorize the app)\n")

    server = HTTPServer(('localhost', 8080), CallbackHandler)
    server.handle_request()  # Handle one request and stop

    return auth_code

def exchange_code_for_tokens(code):
    """Step 2: Exchange authorization code for tokens"""
    import urllib.request
    import urllib.parse
    import json

    print("\n📋 Step 2: Exchanging authorization code for tokens...")

    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'client_id': APP_KEY,
        'client_secret': APP_SECRET
    }

    # Encode data
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')

    # Make request
    try:
        req = urllib.request.Request(TOKEN_URL, data=encoded_data, method='POST')
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            tokens = json.loads(response_data)
            return tokens
    except urllib.error.HTTPError as e:
        print(f"\n❌ Error: {e.code}")
        print(e.read().decode('utf-8'))
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

def get_dropbox_user_info(access_token):
    """Get Dropbox account info"""
    import urllib.request
    import json

    try:
        req = urllib.request.Request(
            "https://api.dropboxapi.com/2/users/get_current_account",
            method='POST'
        )
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            user_info = json.loads(response_data)
            return user_info
    except Exception as e:
        print(f"\n⚠️  Could not fetch user info: {str(e)}")
        return None

def main():
    try:
        # Step 1: Get authorization code
        code = get_authorization_code()

        if not code:
            print("\n❌ Failed to get authorization code")
            sys.exit(1)

        print(f"✅ Authorization code received: {code[:20]}...")

        # Step 2: Exchange for tokens
        tokens = exchange_code_for_tokens(code)

        if not tokens:
            print("\n❌ Failed to exchange code for tokens")
            sys.exit(1)

        # Step 3: Get user info
        user_info = get_dropbox_user_info(tokens['access_token'])

        # Display tokens
        print("\n" + "="*50)
        print("✅ SUCCESS! Your Dropbox tokens:")
        print("="*50)

        if user_info:
            print(f"\n👤 Dropbox Account:")
            print(f"   Name: {user_info.get('name', {}).get('display_name', 'N/A')}")
            print(f"   Email: {user_info.get('email', 'N/A')}")
            print(f"   Account ID: {user_info.get('account_id', 'N/A')}")

        print(f"\nAccess Token (expires in ~4 hours):")
        print(f"{tokens['access_token'][:50]}...")
        print(f"\n🔑 REFRESH TOKEN (SAVE THIS!):")
        print(f"{tokens['refresh_token']}")
        print("\n" + "="*50)
        print("\n📋 Add this to Railway environment variables:")
        print("="*50)
        print(f"DROPBOX_APP_KEY={APP_KEY}")
        print(f"DROPBOX_APP_SECRET={APP_SECRET}")
        print(f"DROPBOX_REFRESH_TOKEN={tokens['refresh_token']}")
        print("="*50)

        print("\n✅ Done! Add these variables to Railway.\n")

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
