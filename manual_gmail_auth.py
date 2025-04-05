"""
Manual Gmail OAuth Authorization

This script implements a manual OAuth flow for Gmail API using direct HTTP requests
instead of relying on Google's OAuth libraries. This provides a more transparent
authentication process and allows for better error handling.
"""

import os
import json
import base64
import pickle
import requests
from urllib.parse import urlencode, quote
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file (USER_EMAIL, etc.)
load_dotenv()

# Configuration for OAuth authentication
CLIENT_SECRET_FILE = 'client_secret_819038297150-71h5nap5siu85uh3eti1vhf3hpnm71c6.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.json'  # Will store the access & refresh tokens
# Use a simpler scope that doesn't require verification
# SCOPES = ['https://www.googleapis.com/auth/gmail.send']
SCOPES = ['https://mail.google.com/']  # Full mail access - works better for testing
OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'  # Google's OAuth authorization endpoint
OAUTH_TOKEN_URL = 'https://oauth2.googleapis.com/token'  # Google's OAuth token endpoint
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'  # Out-of-band (manual) authorization code flow
USER_EMAIL = os.getenv("USER_EMAIL", "your.email@gmail.com")  # Email from .env or default

def load_client_secrets():
    """Load the client secrets from the JSON file
    
    Returns:
        dict: The client secrets data or None if the file is invalid/missing
    """
    try:
        if not os.path.exists(CLIENT_SECRET_FILE):
            print(f"ERROR: Client secret file not found: {CLIENT_SECRET_FILE}")
            return None
            
        with open(CLIENT_SECRET_FILE, 'r') as f:
            client_secrets = json.load(f)
            
        if 'installed' not in client_secrets:
            print("ERROR: Invalid client secret file format")
            return None
            
        return client_secrets['installed']
    except Exception as e:
        print(f"ERROR loading client secrets: {str(e)}")
        return None

def generate_auth_url(client_id):
    """Generate the authorization URL for the OAuth flow
    
    Args:
        client_id (str): The OAuth client ID from the client secrets file
        
    Returns:
        str: A URL that the user can visit to authorize the application
    """
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(SCOPES),
        'response_type': 'code',
        'access_type': 'offline',  # Get a refresh token for long-term access
        'prompt': 'consent',  # Force user to see the consent screen
        'login_hint': USER_EMAIL  # Pre-fill the user's email
    }
    
    # Convert the params to a URL-encoded string
    param_string = '&'.join([f"{k}={quote(v, safe='')}" for k, v in params.items()])
    return f"{OAUTH_AUTH_URL}?{param_string}"

def exchange_code_for_tokens(client_id, client_secret, auth_code):
    """Exchange the authorization code for access and refresh tokens
    
    Args:
        client_id (str): The OAuth client ID
        client_secret (str): The OAuth client secret
        auth_code (str): The authorization code from the user
        
    Returns:
        dict: Token data including access_token and refresh_token, or None on failure
    """
    token_request = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(OAUTH_TOKEN_URL, data=token_request)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"ERROR: Failed to exchange code for tokens")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def refresh_access_token(client_id, client_secret, refresh_token):
    """Get a new access token using the refresh token
    
    Args:
        client_id (str): The OAuth client ID
        client_secret (str): The OAuth client secret
        refresh_token (str): The refresh token to use
        
    Returns:
        str: A new access token or None on failure
    """
    token_request = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(OAUTH_TOKEN_URL, data=token_request)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('access_token')
    else:
        print(f"ERROR: Failed to refresh access token")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_valid_tokens():
    """Get valid tokens, refreshing if necessary
    
    This function will:
    1. Look for existing tokens in the token file
    2. If tokens exist, refresh the access token
    3. If no tokens exist or refreshing fails, start a new OAuth flow
    
    Returns:
        dict: Token data including access_token and refresh_token, or None on failure
    """
    client_secrets = load_client_secrets()
    if not client_secrets:
        return None
    
    client_id = client_secrets['client_id']
    client_secret = client_secrets['client_secret']
    
    # Check if we have existing tokens
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        
        # If we have a refresh token, use it to get a new access token
        if 'refresh_token' in token_data:
            print("Refreshing access token...")
            new_access_token = refresh_access_token(
                client_id,
                client_secret,
                token_data['refresh_token']
            )
            
            if new_access_token:
                token_data['access_token'] = new_access_token
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(token_data, f)
                return token_data
    
    # If we don't have tokens or couldn't refresh, start the authorization flow
    auth_url = generate_auth_url(client_id)
    
    print("\n" + "=" * 70)
    print("AUTHORIZATION REQUIRED")
    print("=" * 70)
    print("\nFollow these steps:")
    print("1. Copy and paste this URL into your browser:")
    print(f"\n{auth_url}\n")
    print("2. Sign in with your Google account")
    print("3. You may see a warning about unverified app - try these options:")
    print("   - Click 'Advanced' and then 'Go to [App Name] (unsafe)'")
    print("   - OR if you're using a personal Google Cloud project, you can add yourself")
    print("     as a test user in the Google Cloud Console under:")
    print("     'APIs & Services' > 'OAuth consent screen' > 'Test users'")
    print("4. Allow the permissions requested")
    print("5. Copy the authorization code provided")
    
    auth_code = input("\nEnter the authorization code: ")
    
    # Exchange the authorization code for tokens
    token_data = exchange_code_for_tokens(client_id, client_secret, auth_code)
    
    if token_data:
        # Save the tokens for future use
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
        return token_data
    
    return None

def send_gmail_message(to, subject, message_text):
    """Send an email message using the Gmail API
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject
        message_text (str): Email body text
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    token_data = get_valid_tokens()
    if not token_data:
        print("ERROR: Could not get valid tokens")
        return False
    
    access_token = token_data['access_token']
    
    try:
        # Create a MIME message for the email
        email_message = MIMEMultipart()
        email_message['to'] = to
        email_message['subject'] = subject
        
        # Add text part
        msg = MIMEText(message_text)
        email_message.attach(msg)
        
        # Encode the message in URL-safe base64 format as required by Gmail API
        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode()
        
        # Build the API request to send the message
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json'
        }
        data = {'raw': raw_message}
        
        # Send the request to Gmail API
        print(f"Sending email to {to}...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"Email sent successfully!")
            return True
        else:
            print(f"ERROR: Failed to send email")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR sending email: {str(e)}")
        return False

def provide_testing_instructions():
    """Provide instructions for adding test users to the project
    
    This function prints helpful information about how to handle OAuth verification
    issues when the app is not verified by Google.
    """
    print("\n" + "=" * 70)
    print("GOOGLE OAUTH TESTING INSTRUCTIONS")
    print("=" * 70)
    print("\nIf you're encountering 'App not verified' errors, you have two options:")
    print("\n1. ADD YOURSELF AS A TEST USER (Recommended):")
    print("   a. Go to https://console.cloud.google.com/")
    print("   b. Select the project (look for '819038297150' in the project ID)")
    print("   c. Go to 'APIs & Services' > 'OAuth consent screen'")
    print("   d. Scroll down to 'Test users' section and click 'ADD USERS'")
    print(f"   e. Add your email address: {USER_EMAIL}")
    print("   f. Save and try the authorization process again")
    print("\n2. USE A DIFFERENT SCOPE:")
    print("   - This script now uses 'https://mail.google.com/' scope which may work better") 
    print("     for testing, but grants broader access")
    print("\n3. ALTERNATIVE AUTHENTICATION:")
    print("   - Consider using SMTP with App Passwords if OAuth is problematic")
    print("   - App Passwords can be created in your Google Account security settings")
    print("=" * 70)

if __name__ == "__main__":
    print("Manual Gmail OAuth Authorization")
    print("-------------------------------\n")
    
    # Provide testing instructions first
    provide_testing_instructions()
    
    # Ask user if they want to continue
    cont = input("\nDo you want to proceed with OAuth authorization? (y/n): ").lower()
    if cont != 'y':
        print("Exiting. Please try again after adding yourself as a test user.")
        exit(0)
    
    # Test sending an email
    recipient = USER_EMAIL  # Send to ourselves as a test
    subject = "Test Email via OAuth"
    body = "This is a test email sent using OAuth 2.0 authentication."
    
    success = send_gmail_message(recipient, subject, body)
    
    if success:
        print("\nSUCCESS: Email was sent successfully!")
        print(f"OAuth tokens are saved in {os.path.abspath(TOKEN_FILE)}")
    else:
        print("\nFAILED: Email could not be sent. Check the error messages above.") 