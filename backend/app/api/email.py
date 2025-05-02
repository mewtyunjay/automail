# backend/app/api/email.py
from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any

from app.services.gmail_client import GmailClient
from app.agents.summarizer import SummarizerAgent

router = APIRouter()
gmail_client = GmailClient()
summarizer = SummarizerAgent()


@router.get("/test")
def test_email():
    """
    Test endpoint to check if the backend can connect to Gmail API using current credentials.
    """
    try:
        labels = gmail_client.get_labels()
        return {"msg": "Successfully connected to Gmail API", "label_count": len(labels)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail API connection failed: {str(e)}")

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
    query: str = Query("", description="Gmail search query")):
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
    label_id: str = Path(..., description="ID of the label to add")):
    """
    Add a label to a message.

    This endpoint adds a specified label to a message with the given ID.

    Args:
        message_id: ID of the message to which the label will be added.
        label_id: ID of the label to add to the message.

    Returns:
        A success message if the label was added successfully. Otherwise, raises an HTTPException.
    """
    try:
        success = gmail_client.add_label_to_message(message_id, label_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to add label {label_id} to message {message_id}")
        return {
            "success": True,
            "message_id": message_id,
            "label_id": label_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/messages/{message_id}/labels/{label_id}")
def remove_label(
    message_id: str = Path(..., description="ID of the message"),
    label_id: str = Path(..., description="ID of the label to remove")):
    """
    Removes a specified label from a message with the given ID.

    Args:
        message_id: ID of the message from which the label will be removed.
        label_id: ID of the label to remove from the message.

    Returns:
        A success message if the label was removed successfully. Otherwise, raises an HTTPException.
    """
    try:
        success = gmail_client.remove_label_from_message(message_id, label_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to remove label {label_id} from message {message_id}")
        return {
            "success": True,
            "message_id": message_id,
            "label_id": label_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/{message_id}/mark_read")
def mark_as_read(message_id: str = Path(..., description="ID of the message")):
    """
    Mark a message as read by removing the UNREAD label.
    """
    try:
        success = gmail_client.remove_label_from_message(message_id, "UNREAD")
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to mark message {message_id} as read")
        return {"success": True, "message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/messages/{message_id}/mark_unread")
def mark_as_unread(message_id: str = Path(..., description="ID of the message")):
    """
    Mark a message as unread by adding the UNREAD label.
    """
    try:
        success = gmail_client.add_label_to_message(message_id, "UNREAD")
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to mark message {message_id} as unread")
        return {"success": True, "message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/messages/{message_id}/summary")
def summarize_message(message_id: str = Path(..., description="ID of the message to summarize")):
    """
    Summarize a specific email message.

    Args:
        message_id: ID of the message to summarize

    Returns:
        A dictionary containing the summary of the message as a string
    """
    try:
        summary = summarizer.run(message_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize-content", response_model=str)
async def summarize_content(content: str = Body(..., embed=True)) -> str:
    """Summarize email content directly passed in the request body."""
    try:
        # Use the correct methods from SummarizerAgent
        prompt = summarizer.compose_prompt(content)
        summary = summarizer.call_agent(prompt)
        if not summary:
             raise HTTPException(status_code=500, detail="Summarization failed or returned empty.")
        return summary
    except Exception as e:
        # Log the exception details if you have logging configured
        # logger.error(f"Error summarizing content: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Error during summarization: {str(e)}")