# backend/app/api/auth.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from app.core import auth as core_auth
import logging

router = APIRouter()

@router.get("/login")
def login():
    """
    Redirect user to Google OAuth consent screen.
    Returns a 500 error if auth URL cannot be generated.
    """
    try:
        url = core_auth.get_google_auth_url()
        logging.info(f"Redirecting to Google OAuth: {url}")
        return RedirectResponse(url)
    except Exception as e:
        logging.error(f"/auth/login error: {e}")
        raise HTTPException(status_code=500, detail="Could not generate Google OAuth URL. Check credentials.")

@router.get("/callback")
def callback(request: Request):
    """
    Handle Google OAuth callback, exchange code for tokens, save token, and redirect or respond.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")
    try:
        token = core_auth.exchange_code_for_token(code)
        core_auth.save_token(token)
        logging.info("OAuth token successfully obtained and saved.")
        # Redirect to a frontend page or show success message
        return RedirectResponse(url="/", status_code=302)
    except Exception as e:
        logging.error(f"/auth/callback error: {e}")
        # Return a more user-friendly error page
        error_html = f"""
        <html>
            <head><title>Authentication Error</title></head>
            <body>
                <h1>Authentication Failed</h1>
                <p>There was an error during authentication. Please try again.</p>
                <p>Error details: {str(e)}</p>
                <p><a href="/auth/login">Try again</a></p>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=400)

@router.get("/me")
def me():
    """
    Get user info from token. Optionally refresh token if needed.
    Returns 401 if not authenticated or token expired and cannot be refreshed.
    """
    token = core_auth.load_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in via /auth/login.")
    access_token = token.get("access_token")
    try:
        user_info = core_auth.get_user_info(access_token)
        return user_info
    except Exception as e:
        logging.warning(f"/auth/me: Access token failed, attempting refresh. Error: {e}")
        refresh_token = token.get("refresh_token")
        if refresh_token:
            try:
                new_token = core_auth.refresh_access_token(refresh_token)
                core_auth.save_token({**token, **new_token})
                access_token = new_token.get("access_token")
                user_info = core_auth.get_user_info(access_token)
                return user_info
            except Exception as e2:
                logging.error(f"/auth/me: Token refresh failed: {e2}")
                raise HTTPException(status_code=401, detail="Token expired and refresh failed. Please re-authenticate.")
        else:
            raise HTTPException(status_code=401, detail="Token expired and no refresh token available. Please re-authenticate.")
