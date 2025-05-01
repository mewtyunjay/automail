# backend/app/api/email.py
from fastapi import APIRouter
import os
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

router = APIRouter()

@router.get("/test")
def test_email():
    return {"msg": "Email endpoint working"}

@router.get("/gmailapitest")
def gmail_api_test():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'token.json')
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"Could not refresh credentials: {e}")
        else:
            raise HTTPException(status_code=401, detail="No valid Gmail credentials. Please authenticate manually using the script.")
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        return {"labels": [label['name'] for label in labels]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

