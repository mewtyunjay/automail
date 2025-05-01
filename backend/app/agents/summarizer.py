import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv
from app.services.gmail_client import GmailClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class SummarizerAgent:
    """Agent that summarizes emails."""
    
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

    def run(self, message_id: str) -> str:
        """Run the summarizer agent on the given message.
        
        Args:
            message_id: The ID of the message to summarize
            
        Returns:
            The summary text
            
        Raises:
            Exception: If there is an error summarizing the message
        """
        try:
            # Fetch email from Gmail API
            email_data = self.gmail.get_message(message_id)
            body = email_data.get("body_plain") or email_data.get("body_html", "")
            
            if not body:
                logger.warning(f"No email body found for message {message_id}")
                raise ValueError("No email content found")
            
            prompt = self.compose_prompt(body)
            summary = self.call_agent(prompt)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing message {message_id}: {str(e)}")
            raise

    def _get_user_rules(self) -> Optional[str]:
        try:
            rules_path = Path(__file__).parent / "user_rules.txt"
            if not rules_path.exists() or rules_path.stat().st_size == 0:
                logger.info("User rules file is empty or doesn't exist")
                return None
                
            with open(rules_path, "r") as f:
                rules = f.read().strip()
                
            if not rules:
                logger.info("User rules file is empty")
                return None
                
            logger.info("User rules loaded successfully")
            return rules
        except Exception as e:
            logger.error(f"Error reading user rules: {str(e)}")
            return None
    
    def compose_prompt(self, email_text: str) -> str:
        base_prompt = f"""Summarize the following email concisely. Include key points, action items, and important details.
        If there are attachments or links, mention them briefly.
        """
        
        user_rules = None
        if self.use_memory:
            user_rules = self._get_user_rules()
            
        if user_rules:
            prompt = f"{base_prompt}\n\nUser Rules:\n{user_rules}\n\nEmail Content:\n{email_text}"
        else:
            prompt = f"{base_prompt}\n\nEmail Content:\n{email_text}"
        
        return prompt

    def call_agent(self, prompt: str) -> str:
        try:
            response = self.agent.run(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error calling agent: {str(e)}")
            raise
