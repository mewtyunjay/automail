# backend/app/api/email.py
from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any

from app.services.gmail_client import GmailClient
from app.agents.summarizer import SummarizerAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.todo_agent import TodoAgent
from app.agents.reminder_agent import ReminderAgent
from app.agents.nyu_agent import NYUAgent

router = APIRouter()
gmail_client = GmailClient()
summarizer = SummarizerAgent()
finance_agent = FinanceAgent()
todo_agent = TodoAgent()
reminder_agent = ReminderAgent()
nyu_agent = NYUAgent()


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
        finance_data = finance_agent.run(message_id)
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
        todos_data = todo_agent.run(message_id)
        if not todos_data:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found or contains no todo items")
        return {"todos_data": todos_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}/reminders")
def extract_reminders(message_id: str = Path(..., description="ID of the message to extract reminders from")):
    """
    Extract reminders and scheduled events from a specific email message.

    Args:
        message_id: ID of the message to process

    Returns:
        A dictionary containing structured reminder data
    """
    try:
        reminders_data = reminder_agent.run(message_id)
        if not reminders_data:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found or contains no reminders")
        return {"reminders_data": reminders_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}/nyu")
def extract_nyu_info(message_id: str = Path(..., description="ID of the message to extract NYU information from")):
    """
    Extract NYU-related information from a specific email message.

    Args:
        message_id: ID of the message to process

    Returns:
        A dictionary containing structured NYU-related data
    """
    try:
        nyu_data = nyu_agent.run(message_id)
        if not nyu_data:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found or contains no NYU information")
        return {"nyu_data": nyu_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/process-content/finance")
# async def process_finance_content(content: str = Body(..., embed=True)) -> Dict[str, Any]:
#     """Extract financial information from email content directly passed in the request body."""
#     try:
#         prompt = finance_agent.compose_prompt(content)
#         finance_data = finance_agent.call_agent(prompt)
#         if not finance_data:
#             raise HTTPException(status_code=500, detail="Financial extraction failed or returned empty.")
#         return {"finance_data": finance_data}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during financial extraction: {str(e)}")


# @router.post("/process-content/todos")
# async def process_todos_content(content: str = Body(..., embed=True)) -> Dict[str, Any]:
#     """Extract todo items from email content directly passed in the request body."""
#     try:
#         # We need to pass empty subject as it's required by the todo_agent
#         prompt = todo_agent.compose_prompt("", content)
#         todos_data = todo_agent.call_agent(prompt)
#         if not todos_data:
#             raise HTTPException(status_code=500, detail="Todo extraction failed or returned empty.")
#         return {"todos_data": todos_data}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during todo extraction: {str(e)}")


# @router.post("/process-content/reminders")
# async def process_reminders_content(content: str = Body(..., embed=True)) -> Dict[str, Any]:
#     """Extract reminders from email content directly passed in the request body."""
#     try:
#         # We need to pass empty subject and date as they're required by the reminder_agent
#         prompt = reminder_agent.compose_prompt("", content, "")
#         reminders_data = reminder_agent.call_agent(prompt)
#         if not reminders_data:
#             raise HTTPException(status_code=500, detail="Reminder extraction failed or returned empty.")
#         return {"reminders_data": reminders_data}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during reminder extraction: {str(e)}")


# @router.post("/process-content/nyu")
# async def process_nyu_content(content: str = Body(..., embed=True)) -> Dict[str, Any]:
#     """Extract NYU-related information from email content directly passed in the request body."""
#     try:
#         # We need to pass empty subject and sender as they're required by the nyu_agent
#         prompt = nyu_agent.compose_prompt("", "", content)
#         nyu_data = nyu_agent.call_agent(prompt)
#         if not nyu_data:
#             raise HTTPException(status_code=500, detail="NYU information extraction failed or returned empty.")
#         return {"nyu_data": nyu_data}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during NYU information extraction: {str(e)}")