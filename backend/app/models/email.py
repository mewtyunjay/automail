from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base

# Association table for many-to-many relationship between emails and labels
email_label_association = Table(
    'email_label_association',
    Base.metadata,
    Column('email_id', String, ForeignKey('emails.message_id')),
    Column('label_id', String, ForeignKey('labels.label_id'))
)

class Email(Base):
    """Model for storing email metadata."""
    __tablename__ = "emails"

    message_id = Column(String, primary_key=True, index=True)
    thread_id = Column(String, index=True)
    subject = Column(String, nullable=True)
    sender = Column(String)
    recipient = Column(String)
    date_received = Column(DateTime)
    snippet = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    has_attachments = Column(Boolean, default=False)
    
    # Store additional metadata as JSON
    email_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    labels = relationship("Label", secondary=email_label_association, back_populates="emails")
    reminders = relationship("Reminder", back_populates="email")
    todos = relationship("Todo", back_populates="email")
    finance_data = relationship("FinanceData", back_populates="email")

class Label(Base):
    """Model for storing Gmail labels."""
    __tablename__ = "labels"

    label_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String)  # system or user
    
    # Relationships
    emails = relationship("Email", secondary=email_label_association, back_populates="labels")

class Reminder(Base):
    """Model for storing reminders extracted from emails."""
    __tablename__ = "reminders"

    id = Column(String, primary_key=True)
    email_id = Column(String, ForeignKey("emails.message_id"))
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    email = relationship("Email", back_populates="reminders")

class Todo(Base):
    """Model for storing todo items extracted from emails."""
    __tablename__ = "todos"

    id = Column(String, primary_key=True)
    email_id = Column(String, ForeignKey("emails.message_id"))
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=True)  # high, medium, low
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    email = relationship("Email", back_populates="todos")

class FinanceData(Base):
    """Model for storing financial information extracted from emails."""
    __tablename__ = "finance_data"

    id = Column(String, primary_key=True)
    email_id = Column(String, ForeignKey("emails.message_id"))
    amount = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    transaction_purpose = Column(String, nullable=True)  # purchase, refund, payment, bill, statement, etc.
    transaction_type = Column(String, nullable=True)  # credit or debit
    category = Column(String, nullable=True)  # spending category (dining, travel, utilities, etc.)
    due_date = Column(DateTime, nullable=True)
    details = Column(JSONB, nullable=True)  # Additional extracted financial details
    
    # Relationships
    email = relationship("Email", back_populates="finance_data")
