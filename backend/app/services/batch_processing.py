# backend/app/services/batch_processing.py
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.gmail_client import GmailClient
from app.agents.summarizer import SummarizerAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.todo_agent import TodoAgent
from app.agents.reminder_agent import ReminderAgent
from app.db.repositories import EmailRepository, LabelRepository, ReminderRepository, TodoRepository, FinanceRepository

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchProcessor:
    """Service for batch processing emails through various agents and storing results in the database."""
    
    def __init__(self):
        self.gmail_client = GmailClient()
        self.summarizer = SummarizerAgent()
        self.finance_agent = FinanceAgent()
        self.todo_agent = TodoAgent()
        self.reminder_agent = ReminderAgent()
    
    def process_recent_emails(self, db: Session, max_emails: int = 10, query: str = "") -> Dict[str, Any]:
        """Process the most recent emails and store results in the database.
        
        Args:
            db: Database session
            max_emails: Maximum number of emails to process
            query: Optional Gmail search query to filter emails
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = datetime.now()
        logger.info(f"Starting batch processing of up to {max_emails} emails")
        
        # Get recent emails
        try:
            emails = self.gmail_client.get_messages(max_results=max_emails, query=query)
            logger.info(f"Retrieved {len(emails)} emails from Gmail")
        except Exception as e:
            logger.error(f"Error retrieving emails: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to retrieve emails: {str(e)}",
                "processed_count": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
        
        # Process statistics
        stats = {
            "total_emails": len(emails),
            "emails_processed": 0,
            "emails_failed": 0,
            "reminders_extracted": 0,
            "todos_extracted": 0,
            "finance_data_extracted": 0,
            "failed_emails": []
        }
        
        # Process each email
        for email in emails:
            try:
                self._process_single_email(db, email, stats)
                stats["emails_processed"] += 1
            except Exception as e:
                logger.error(f"Error processing email {email.get('id')}: {str(e)}")
                stats["emails_failed"] += 1
                stats["failed_emails"].append({
                    "email_id": email.get('id'),
                    "error": str(e)
                })
        
        # Calculate duration
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Prepare result
        result = {
            "success": True,
            "stats": stats,
            "duration_seconds": duration_seconds,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        logger.info(f"Batch processing completed in {duration_seconds:.2f} seconds")
        logger.info(f"Processed {stats['emails_processed']} emails successfully")
        logger.info(f"Failed to process {stats['emails_failed']} emails")
        
        return result
    
    def _process_single_email(self, db: Session, email: Dict[str, Any], stats: Dict[str, Any]) -> None:
        """Process a single email through all agents and store results.
        
        Args:
            db: Database session
            email: Email data from Gmail API
            stats: Statistics dictionary to update
        """
        email_id = email.get('id')
        logger.info(f"Processing email {email_id}")
        
        # Save email to database
        db_email = EmailRepository.create_or_update_email(db, email)
        
        # Save labels
        if 'labelIds' in email:
            for label_id in email['labelIds']:
                # Create or update label
                label_data = {'id': label_id, 'name': label_id}  # Basic label data
                LabelRepository.create_or_update_label(db, label_data)
                
                # Associate label with email
                EmailRepository.add_label_to_email(db, email_id, label_id)
        
        # Process with reminder agent
        try:
            reminders_data = self.reminder_agent.run(email_id)
            if reminders_data and isinstance(reminders_data, dict) and "reminders" in reminders_data:
                for reminder in reminders_data["reminders"]:
                    if reminder and isinstance(reminder, dict) and "title" in reminder:
                        # Convert to the format expected by the repository
                        reminder_item = {
                            "description": reminder.get("title", ""),
                            "due_date": reminder.get("date"),
                            "is_completed": False
                        }
                        ReminderRepository.create_reminder(db, email_id, reminder_item)
                        stats["reminders_extracted"] += 1
        except Exception as e:
            logger.warning(f"Error extracting reminders from email {email_id}: {str(e)}")
        
        # Process with todo agent
        try:
            todos_data = self.todo_agent.run(email_id)
            if todos_data and isinstance(todos_data, dict) and "todos" in todos_data:
                for todo in todos_data["todos"]:
                    if todo and isinstance(todo, dict) and "task" in todo:
                        # Convert to the format expected by the repository
                        todo_item = {
                            "description": todo.get("task", ""),
                            "priority": todo.get("priority", "medium"),
                            "is_completed": False
                        }
                        TodoRepository.create_todo(db, email_id, todo_item)
                        stats["todos_extracted"] += 1
        except Exception as e:
            logger.warning(f"Error extracting todos from email {email_id}: {str(e)}")
        
        # Process with finance agent
        try:
            finance_data = self.finance_agent.run(email_id)
            if finance_data and isinstance(finance_data, dict) and "error" not in finance_data:
                # Finance agent returns a single object, not a list
                if any(key in finance_data for key in ["amount", "transaction_purpose", "transaction_type", "merchant"]):
                    FinanceRepository.create_finance_data(db, email_id, finance_data)
                    stats["finance_data_extracted"] += 1
        except Exception as e:
            logger.warning(f"Error extracting finance data from email {email_id}: {str(e)}")
        
        logger.info(f"Completed processing email {email_id}")

# Create a singleton instance
batch_processor = BatchProcessor()