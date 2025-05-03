from typing import List, Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from datetime import datetime
import email.utils
import logging

logger = logging.getLogger(__name__)

from app.models.email import Email, Label, Reminder, Todo, FinanceData

class EmailRepository:
    """Repository for email-related database operations."""
    
    @staticmethod
    def create_or_update_email(db: Session, email_data: Dict[str, Any]) -> Email:
        """
        Create a new email record or update if it already exists.
        
        Args:
            db: Database session
            email_data: Dictionary containing email data from Gmail API
            
        Returns:
            Email object
        """
        # Check if email already exists
        existing_email = db.query(Email).filter(Email.message_id == email_data.get('id')).first()
        
        if existing_email:
            # Update existing email
            for key, value in email_data.items():
                if key == 'id':
                    continue  # Skip the ID field
                if hasattr(existing_email, key):
                    setattr(existing_email, key, value)
            
            db.commit()
            return existing_email
        
        # Create new email
        # Parse the date string from Gmail to a datetime object
        date_received = None
        date_str = email_data.get('date')
        if date_str:
            try:
                # Try parsing with email.utils.parsedate_to_datetime
                date_received = email.utils.parsedate_to_datetime(date_str)
            except Exception as e:
                logger.warning(f"Failed to parse date '{date_str}' with email.utils: {str(e)}")
                try:
                    # Fallback: try to parse the date manually
                    # Remove the (UTC) part if present
                    date_str = date_str.split(' (')[0].strip()
                    date_received = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                except Exception as e2:
                    logger.error(f"Failed to parse date '{date_str}' with fallback method: {str(e2)}")
                    # Use current time as a last resort
                    date_received = datetime.now()
        else:
            # If no date provided, use current time
            date_received = datetime.now()
            
        email = Email(
            message_id=email_data.get('id'),
            thread_id=email_data.get('threadId'),
            subject=email_data.get('subject'),
            sender=email_data.get('from'),
            recipient=email_data.get('to'),
            date_received=date_received,
            snippet=email_data.get('snippet'),
            is_read=not email_data.get('labelIds', {}).get('UNREAD', False),
            has_attachments=bool(email_data.get('attachments')),
            email_metadata=email_data.get('metadata', {})
        )
        
        db.add(email)
        db.commit()
        db.refresh(email)
        return email
    
    @staticmethod
    def get_email_by_id(db: Session, message_id: str) -> Optional[Email]:
        """
        Get an email by its message ID.
        
        Args:
            db: Database session
            message_id: Gmail message ID
            
        Returns:
            Email object if found, None otherwise
        """
        return db.query(Email).filter(Email.message_id == message_id).first()
    
    @staticmethod
    def get_emails(db: Session, skip: int = 0, limit: int = 100) -> List[Email]:
        """
        Get a list of emails with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Email objects
        """
        return db.query(Email).order_by(Email.date_received.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def add_label_to_email(db: Session, message_id: str, label_id: str) -> bool:
        """
        Add a label to an email.
        
        Args:
            db: Database session
            message_id: Gmail message ID
            label_id: Gmail label ID
            
        Returns:
            True if successful, False otherwise
        """
        email = EmailRepository.get_email_by_id(db, message_id)
        label = LabelRepository.get_label_by_id(db, label_id)
        
        if not email or not label:
            return False
        
        email.labels.append(label)
        db.commit()
        return True
    
    @staticmethod
    def remove_label_from_email(db: Session, message_id: str, label_id: str) -> bool:
        """
        Remove a label from an email.
        
        Args:
            db: Database session
            message_id: Gmail message ID
            label_id: Gmail label ID
            
        Returns:
            True if successful, False otherwise
        """
        email = EmailRepository.get_email_by_id(db, message_id)
        label = LabelRepository.get_label_by_id(db, label_id)
        
        if not email or not label:
            return False
        
        if label in email.labels:
            email.labels.remove(label)
            db.commit()
        
        return True

class LabelRepository:
    """Repository for label-related database operations."""
    
    @staticmethod
    def create_or_update_label(db: Session, label_data: Dict[str, Any]) -> Label:
        """
        Create a new label or update if it already exists.
        
        Args:
            db: Database session
            label_data: Dictionary containing label data from Gmail API
            
        Returns:
            Label object
        """
        # Check if label already exists
        existing_label = db.query(Label).filter(Label.label_id == label_data.get('id')).first()
        
        if existing_label:
            # Update existing label
            existing_label.name = label_data.get('name', existing_label.name)
            existing_label.type = label_data.get('type', existing_label.type)
            
            db.commit()
            return existing_label
        
        # Create new label
        label = Label(
            label_id=label_data.get('id'),
            name=label_data.get('name'),
            type=label_data.get('type', 'user')
        )
        
        db.add(label)
        db.commit()
        db.refresh(label)
        return label
    
    @staticmethod
    def get_label_by_id(db: Session, label_id: str) -> Optional[Label]:
        """
        Get a label by its ID.
        
        Args:
            db: Database session
            label_id: Gmail label ID
            
        Returns:
            Label object if found, None otherwise
        """
        return db.query(Label).filter(Label.label_id == label_id).first()
    
    @staticmethod
    def get_labels(db: Session) -> List[Label]:
        """
        Get all labels.
        
        Args:
            db: Database session
            
        Returns:
            List of Label objects
        """
        return db.query(Label).all()

class ReminderRepository:
    """Repository for reminder-related database operations."""
    
    @staticmethod
    def create_reminder(db: Session, email_id: str, reminder_data: Dict[str, Any]) -> Reminder:
        """
        Create a new reminder for an email.
        
        Args:
            db: Database session
            email_id: Gmail message ID
            reminder_data: Dictionary containing reminder data
            
        Returns:
            Reminder object
        """
        reminder = Reminder(
            id=str(uuid4()),
            email_id=email_id,
            description=reminder_data.get('description'),
            due_date=reminder_data.get('due_date'),
            is_completed=reminder_data.get('is_completed', False)
        )
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder
    
    @staticmethod
    def get_reminders_by_email(db: Session, email_id: str) -> List[Reminder]:
        """
        Get all reminders for a specific email.
        
        Args:
            db: Database session
            email_id: Gmail message ID
            
        Returns:
            List of Reminder objects
        """
        return db.query(Reminder).filter(Reminder.email_id == email_id).all()

class TodoRepository:
    """Repository for todo-related database operations."""
    
    @staticmethod
    def create_todo(db: Session, email_id: str, todo_data: Dict[str, Any]) -> Todo:
        """
        Create a new todo item for an email.
        
        Args:
            db: Database session
            email_id: Gmail message ID
            todo_data: Dictionary containing todo data
            
        Returns:
            Todo object
        """
        todo = Todo(
            id=str(uuid4()),
            email_id=email_id,
            description=todo_data.get('description'),
            priority=todo_data.get('priority'),
            is_completed=todo_data.get('is_completed', False)
        )
        
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo
    
    @staticmethod
    def get_todos_by_email(db: Session, email_id: str) -> List[Todo]:
        """
        Get all todo items for a specific email.
        
        Args:
            db: Database session
            email_id: Gmail message ID
            
        Returns:
            List of Todo objects
        """
        return db.query(Todo).filter(Todo.email_id == email_id).all()

class FinanceRepository:
    """Repository for finance-related database operations."""
    
    @staticmethod
    def create_finance_data(db: Session, email_id: str, finance_data: Dict[str, Any]) -> FinanceData:
        """
        Create a new finance record for an email.
        
        Args:
            db: Database session
            email_id: Gmail message ID
            finance_data: Dictionary containing finance data
            
        Returns:
            FinanceData object
        """
        finance = FinanceData(
            id=str(uuid4()),
            email_id=email_id,
            amount=finance_data.get('amount'),
            currency=finance_data.get('currency'),
            transaction_purpose=finance_data.get('transaction_purpose'),
            transaction_type=finance_data.get('transaction_type'),
            category=finance_data.get('category'),
            due_date=finance_data.get('due_date'),
            details=finance_data.get('details', {})
        )
        
        db.add(finance)
        db.commit()
        db.refresh(finance)
        return finance
    
    @staticmethod
    def get_finance_data_by_email(db: Session, email_id: str) -> List[FinanceData]:
        """
        Get all finance records for a specific email.
        
        Args:
            db: Database session
            email_id: Gmail message ID
            
        Returns:
            List of FinanceData objects
        """
        return db.query(FinanceData).filter(FinanceData.email_id == email_id).all()
