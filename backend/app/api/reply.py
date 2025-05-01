# backend/app/api/reply.py
from fastapi import APIRouter, HTTPException, Path, Body
from typing import Dict, Optional
from pydantic import BaseModel

from app.services.gmail_client import GmailClient

router = APIRouter()

# Create a single instance of the Gmail client to be reused
gmail_client = GmailClient()

class ReplyRequest(BaseModel):
    """Request model for replying to an email"""
    body_plain: str
    body_html: Optional[str] = None

@router.get("/test")
def test_reply():
    """Simple test endpoint to check if the reply API is working."""
    return {"msg": "Reply endpoint working"}

@router.post("/message/{message_id}")
def reply_to_message(
    message_id: str = Path(..., description="ID of the message to reply to"),
    reply_data: ReplyRequest = Body(...)
):
    """Reply to a specific email message."""
    try:
        reply_id = gmail_client.reply_to_message(
            message_id=message_id,
            body_plain=reply_data.body_plain,
            body_html=reply_data.body_html
        )
        
        if not reply_id:
            raise HTTPException(status_code=400, detail=f"Failed to reply to message {message_id}")
            
        return {"success": True, "reply_id": reply_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
def send_email(
    to: str = Body(...),
    subject: str = Body(...),
    body_plain: str = Body(...),
    body_html: Optional[str] = Body(None),
    cc: Optional[str] = Body(None),
    bcc: Optional[str] = Body(None)
):
    """Send a new email message."""
    try:
        message_id = gmail_client.send_message(
            to=to,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
            cc=cc,
            bcc=bcc
        )
        
        if not message_id:
            raise HTTPException(status_code=400, detail="Failed to send email")
            
        return {"success": True, "message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))