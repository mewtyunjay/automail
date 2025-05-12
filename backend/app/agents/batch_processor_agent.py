from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.services.gmail_client import GmailClient
from app.agents.summarizer import SummarizerAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.todo_agent import TodoAgent
from app.agents.reminder_agent import ReminderAgent
from app.db.repositories import EmailRepository


class BatchProcessorAgent:
    """
    Agent to process batches of emails through summarization, finance, todos, and reminders.
    """
    def __init__(
        self,
        gmail_client: GmailClient,
        summarizer: SummarizerAgent,
        finance_agent: FinanceAgent,
        todo_agent: TodoAgent,
        reminder_agent: ReminderAgent,
    ):
        self.gmail_client = gmail_client
        self.summarizer = summarizer
        self.finance_agent = finance_agent
        self.todo_agent = todo_agent
        self.reminder_agent = reminder_agent

    def process_recent_emails(
        self,
        db: Session,
        max_emails: int = 20,
        query: str = "",
    ) -> Dict[str, Any]:
        """
        Fetch recent emails, run them through all agents, and assemble a summary.

        Returns a dict with keys "overview" and "details".
        """
        # TODO: implement retrieval of recent email IDs
        # email_ids = EmailRepository.get_recent_email_ids(db, max_emails)
        # TODO: load each email and run agents
        # summaries = [self.summarizer.run(e_id) for e_id in email_ids]
        # todos = [self.todo_agent.run(e_id) for e_id in email_ids]
        # reminders = [self.reminder_agent.run(e_id) for e_id in email_ids]
        # finances = [self.finance_agent.run(e_id) for e_id in email_ids]

        # TODO: build overview + details structure
        return {
            "overview": "",
            "details": []
        }
