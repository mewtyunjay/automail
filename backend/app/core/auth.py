import os
import json
import logging
import requests
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from typing import Dict, Optional

BASE_DIR = Path(os.environ.get("AUTOMAIL_BASE_DIR", Path(__file__).resolve().parent.parent.parent))
CREDENTIALS_PATH = BASE_DIR / "credentials" / "credentials.json"
TOKEN_PATH = BASE_DIR / "credentials" / "token.json"

# Define all possible scopes that might be returned by Google
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/pubsub',
]

def get_google_auth_url() -> str:
    """
    Returns the Google OAuth2 authorization URL for user login/consent.

    Returns:
        str: The authorization URL.
    """
    try:
        flow = Flow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            scopes=SCOPES,
            redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
        )
        # Disable PKCE to avoid scope mismatch issues
        flow.autogenerate_code_verifier = False
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        return auth_url
    except Exception as e:
        logging.error(f"Failed to get Google auth URL: {e}")
        raise

def exchange_code_for_token(code: str) -> Dict:
    """
    Exchanges the authorization code for access and refresh tokens.

    Args:
        code (str): The authorization code.

    Returns:
        Dict: The token dictionary.
    """
    try:
        flow = Flow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            scopes=SCOPES,
            redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
        )
        # Set autogenerate_code_verifier=False to avoid PKCE which might cause issues
        # with scope changes
        flow.autogenerate_code_verifier = False
        # Add include_granted_scopes=True to accept any scopes granted by the user
        flow.fetch_token(code=code)
        creds = flow.credentials
        token = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        }
        return token
    except Exception as e:
        logging.error(f"Failed to exchange code for token: {e}")
        raise

def get_user_info(access_token: str) -> Dict:
    """
    Retrieves user info (email, name, etc.) from Google's userinfo endpoint.

    Args:
        access_token (str): The access token.

    Returns:
        Dict: The user info dictionary.
    """
    try:
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logging.error(f"Failed to get user info: {e}")
        raise

def refresh_access_token(refresh_token: str) -> Dict:
    """
    Refreshes the access token using the refresh token.

    Args:
        refresh_token (str): The refresh token.

    Returns:
        Dict: The new token dictionary.
    """
    try:
        with open(CREDENTIALS_PATH) as f:
            creds_json = json.load(f)["installed"]
        data = {
            "client_id": creds_json["client_id"],
            "client_secret": creds_json["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post("https://oauth2.googleapis.com/token", data=data)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logging.error(f"Failed to refresh token: {e}")
        raise

def save_token(token_dict: Dict) -> None:
    """
    Save token dict to TOKEN_PATH.

    Args:
        token_dict (Dict): The token dictionary.
    """
    with open(TOKEN_PATH, "w") as f:
        json.dump(token_dict, f)

def load_token() -> Optional[Dict]:
    """
    Load token dict from TOKEN_PATH.

    Returns:
        Optional[Dict]: The token dictionary or None if not found.
    """
    if not TOKEN_PATH.exists():
        return None
    with open(TOKEN_PATH) as f:
        return json.load(f)