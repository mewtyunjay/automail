import os
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv
from app.services.gmail_client import GmailClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ReminderAgent:
    """Agent that extracts reminders and scheduled events from emails."""
    
    def __init__(self, use_memory: bool = True):
        self.use_memory = use_memory
        self.gmail = GmailClient()
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
                
            self.agent = Agent(
                model=Gemini(id="gemini-2.0-flash", api_key=api_key),
                markdown=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize Agno agent: {str(e)}")
            raise

    def run(self, message_id: str) -> Dict[str, Any]:
        """Run the reminder extraction agent on the given message.
        
        Args:
            message_id: The ID of the message to extract reminders from
            
        Returns:
            Dictionary containing structured reminder data
            
        Raises:
            Exception: If there is an error processing the message
        """
        try:
            # Fetch email from Gmail API
            email_data = self.gmail.get_message(message_id)
            body = email_data.get("body_plain") or email_data.get("body_html", "")
            subject = email_data.get("subject", "")
            date_str = email_data.get("date", "")
            
            if not body:
                logger.warning(f"No email body found for message {message_id}")
                raise ValueError("No email content found")
            
            prompt = self.compose_prompt(subject, body, date_str)
            reminders_data = self.call_agent(prompt)
            
            return reminders_data
            
        except Exception as e:
            logger.error(f"Error extracting reminders from message {message_id}: {str(e)}")
            raise

    def _get_user_rules(self) -> Optional[str]:
        try:
            rules_path = Path(__file__).parent / "reminder_rules.txt"
            if not rules_path.exists() or rules_path.stat().st_size == 0:
                logger.info("Reminder rules file is empty or doesn't exist")
                return None
                
            with open(rules_path, "r") as f:
                rules = f.read().strip()
                
            if not rules:
                logger.info("Reminder rules file is empty")
                return None
                
            logger.info("Reminder rules loaded successfully")
            return rules
        except Exception as e:
            logger.error(f"Error reading reminder rules: {str(e)}")
            return None
    
    def compose_prompt(self, subject: str, email_text: str, date_str: str) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        base_prompt = f"""Extract all reminders, scheduled events, meetings, deadlines, and important dates from the following email.
        Today's date is {today}.
        
        Return a JSON object with the following structure:
        {{
            "reminders": [
                {{
                    "title": "Brief description of the reminder",
                    "date": "YYYY-MM-DD or null if not specified",
                    "time": "HH:MM or null if not specified", 
                    "location": "Location if applicable or null",
                    "description": "Detailed description or context",
                    "participants": ["List of people involved, if any"],
                    "recurring": true/false,
                    "recurrence_pattern": "daily/weekly/monthly/yearly/custom or null"
                }}
            ],
            "has_time_sensitive_content": true/false
        }}
        
        Only extract genuine reminders and scheduled events - not generic mentions of dates or times.
        Return only valid, parseable JSON. Do not include notes or explanations outside the JSON.
        If no reminders are found, return an empty array for "reminders" and set "has_time_sensitive_content" to false.
        """
        
        user_rules = None
        if self.use_memory:
            user_rules = self._get_user_rules()
            
        if user_rules:
            prompt = f"{base_prompt}\n\nUser Rules:\n{user_rules}\n\nEmail Subject: {subject}\n\nEmail Date: {date_str}\n\nEmail Content:\n{email_text}"
        else:
            prompt = f"{base_prompt}\n\nEmail Subject: {subject}\n\nEmail Date: {date_str}\n\nEmail Content:\n{email_text}"
        
        return prompt

    def call_agent(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.agent.run(prompt)
            # Parse the JSON response
            try:
                # Strip any markdown code block markers if present
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:].strip()
                if content.startswith("```"):
                    content = content[3:].strip()
                if content.endswith("```"):
                    content = content[:-3].strip()
                
                reminders_data = json.loads(content)
                return reminders_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                # Return a structured error response
                return {
                    "error": "Failed to parse reminder data",
                    "raw_response": response.content,
                    "reminders": [],
                    "has_time_sensitive_content": False
                }
        except Exception as e:
            logger.error(f"Error calling agent: {str(e)}")
            raise
