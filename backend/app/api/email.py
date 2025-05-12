# backend/app/api/email.py
from fastapi import APIRouter, HTTPException, Query, Path, Body, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.gmail_client import GmailClient
from app.agents.summarizer import SummarizerAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.todo_agent import TodoAgent
from app.agents.reminder_agent import ReminderAgent
from app.agents.batch_processor_agent import BatchProcessorAgent

# Import database dependencies
from app.db.database import get_db
from app.db.repositories import EmailRepository, LabelRepository, ReminderRepository, TodoRepository, FinanceRepository
from app.models.email import Email, Label, Reminder, Todo, FinanceData

router = APIRouter()
gmail_client = GmailClient()
batch_agent = BatchProcessorAgent(
    gmail_client,
    SummarizerAgent(),
    FinanceAgent(),
    TodoAgent(),
    ReminderAgent(),
)

@router.post("/batch-process")
def batch_process_emails(
    max_emails: int = Query(20, description="Maximum number of emails to process"),
    query: str = Query("", description="Gmail search query to filter emails"),
    db: Session = Depends(get_db)):
    """
    Process a batch of recent emails through all agents and store results in the database.
    
    This endpoint retrieves recent emails from Gmail, processes them through all available
    agents (reminder, todo, finance), and stores the extracted data in the database.
    
    Args:
        max_emails: Maximum number of emails to process (default: 20)
        query: Optional Gmail search query to filter emails
        db: Database session
        
    Returns:
        A dictionary with processing statistics and results
    """
    try:
        result = batch_agent.process_recent_emails(db, max_emails=max_emails, query=query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

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
    query: str = Query("", description="Gmail search query"),
    db: Session = Depends(get_db)):
    """Get messages from Gmail with optional filtering and save to database."""
    try:
        # Get messages from Gmail API
        messages = gmail_client.get_messages(max_results=max_results, query=query)
        
        # Save each message to the database
        for message in messages:
            EmailRepository.create_or_update_email(db, message)
            
            # If the message has labels, save them too
            if 'labelIds' in message:
                for label_id in message['labelIds']:
                    # First ensure the label exists in our database
                    label_data = {'id': label_id, 'name': label_id}  # Basic label data
                    LabelRepository.create_or_update_label(db, label_data)
                    
                    # Then associate the label with the email
                    EmailRepository.add_label_to_email(db, message['id'], label_id)
        
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{message_id}")
def get_message(
    message_id: str = Path(..., description="ID of the message to retrieve"),
    db: Session = Depends(get_db)):
    """Get a specific message by ID and save to database."""
    try:
        # Get message from Gmail API
        message = gmail_client.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        
        # Save the message to the database
        email = EmailRepository.create_or_update_email(db, message)
        
        # If the message has labels, save them too
        if 'labelIds' in message:
            for label_id in message['labelIds']:
                # First ensure the label exists in our database
                label_data = {'id': label_id, 'name': label_id}  # Basic label data
                LabelRepository.create_or_update_label(db, label_data)
                
                # Then associate the label with the email
                EmailRepository.add_label_to_email(db, message['id'], label_id)
        
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/{message_id}/labels/{label_id}")
def add_label(
    message_id: str = Path(..., description="ID of the message"),
    label_id: str = Path(..., description="ID of the label to add"),
    db: Session = Depends(get_db)):
    """
    Add a label to a message and save to database.

    This endpoint adds a specified label to a message with the given ID.

    Args:
        message_id: ID of the message to which the label will be added.
        label_id: ID of the label to add to the message.
        db: Database session

    Returns:
        A success message if the label was added successfully. Otherwise, raises an HTTPException.
    """
    try:
        # Add label in Gmail
        success = gmail_client.add_label_to_message(message_id, label_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to add label {label_id} to message {message_id}")
        
        # First ensure the email exists in our database
        email = EmailRepository.get_email_by_id(db, message_id)
        if not email:
            # If not in database, get it from Gmail and save it
            message = gmail_client.get_message(message_id)
            if message:
                email = EmailRepository.create_or_update_email(db, message)
        
        # Ensure the label exists in our database
        label = LabelRepository.get_label_by_id(db, label_id)
        if not label:
            # If not in database, create a basic label record
            label_data = {'id': label_id, 'name': label_id}  # Basic label data
            label = LabelRepository.create_or_update_label(db, label_data)
        
        # Add the label to the email in our database
        EmailRepository.add_label_to_email(db, message_id, label_id)
        
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
        summary = SummarizerAgent().run(message_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize-content", response_model=str)
async def summarize_content(content: str = Body(..., embed=True)) -> str:
    """Summarize email content directly passed in the request body. Used by extension."""
    try:
        prompt = SummarizerAgent().compose_prompt(content)
        summary = SummarizerAgent().call_agent(prompt)
        if not summary:
             raise HTTPException(status_code=500, detail="Summarization failed or returned empty.")
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during summarization: {str(e)}")

@router.get("/messages/{message_id}/finance")
def extract_finance(message_id: str = Path(..., description="ID of the message to extract financial information from")):
    """
    Extract financial information from a specific email message.

    Args:
        message_id: ID of the message to process

    Returns:
        A dictionary containing structured financial information
    """
    try:
        finance_data = FinanceAgent().run(message_id)
        if not finance_data:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found or contains no financial information")
        return {"finance_data": finance_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{message_id}/todos")
def extract_todos(message_id: str = Path(..., description="ID of the message to extract todo items from")):
    """
    Extract todo items and action items from a specific email message.

    Args:
        message_id: ID of the message to process

    Returns:
        A dictionary containing structured todo items
    """
    try:
        todos_data = TodoAgent().run(message_id)
        if not todos_data:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found or contains no todo items")
        return {"todos_data": todos_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{message_id}/reminders")
def extract_reminders(
    message_id: str = Path(..., description="ID of the message to extract reminders from"),
    db: Session = Depends(get_db)):
    """
    Extract reminders and scheduled events from a specific email message and save to database.

    Args:
        message_id: ID of the message to process
        db: Database session

    Returns:
        A dictionary containing structured reminder data
    """
    try:
        # First ensure the email exists in our database
        email = EmailRepository.get_email_by_id(db, message_id)
        if not email:
            # If not in database, get it from Gmail and save it
            message = gmail_client.get_message(message_id)
            if message:
                email = EmailRepository.create_or_update_email(db, message)
        
        # Extract reminders using the agent
        reminders_data = ReminderAgent().run(message_id)
        if not reminders_data:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found or contains no reminders")
        
        # Save reminders to the database
        saved_reminders = []
        for reminder in reminders_data:
            # Create reminder in database
            db_reminder = ReminderRepository.create_reminder(db, message_id, reminder)
            saved_reminders.append(db_reminder)
        
        return {"reminders_data": reminders_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
