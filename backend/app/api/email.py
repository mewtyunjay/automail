# backend/app/api/email.py
from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any

from app.services.gmail_client import GmailClient

router = APIRouter()

# Create a single instance of the Gmail client to be reused
gmail_client = GmailClient()

@router.get("/test")
def test_email():
    """Simple test endpoint to check if the email API is working."""
    return {"msg": "Email endpoint working"}

@router.get("/labels")
def get_labels():
    """Get all Gmail labels for the authenticated user."""
    try:
        labels = gmail_client.get_labels()
        return {"labels": labels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages")
def get_messages(
    max_results: int = Query(10, description="Maximum number of messages to return"),
    query: str = Query("", description="Gmail search query")
):
    """Get messages from Gmail with optional filtering."""
    try:
        messages = gmail_client.get_messages(max_results=max_results, query=query)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{message_id}")
def get_message(message_id: str = Path(..., description="ID of the message to retrieve")):
    """Get a specific message by ID."""
    try:
        message = gmail_client.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/{message_id}/labels/{label_id}")
def add_label(
    message_id: str = Path(..., description="ID of the message"),
    label_id: str = Path(..., description="ID of the label to add")
):
    """Add a label to a message."""
    try:
        success = gmail_client.add_label_to_message(message_id, label_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to add label {label_id} to message {message_id}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/messages/{message_id}/labels/{label_id}")
def remove_label(
    message_id: str = Path(..., description="ID of the message"),
    label_id: str = Path(..., description="ID of the label to remove")
):
    """Remove a label from a message."""
    try:
        success = gmail_client.remove_label_from_message(message_id, label_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to remove label {label_id} from message {message_id}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

