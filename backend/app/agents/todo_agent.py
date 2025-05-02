import os
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv
from app.services.gmail_client import GmailClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TodoAgent:
    """Agent that extracts todo items and action items from emails."""
    
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
        """Run the todo extraction agent on the given message.
        
        Args:
            message_id: The ID of the message to extract todos from
            
        Returns:
            Dictionary containing structured todo/action items
            
        Raises:
            Exception: If there is an error processing the message
        """
        try:
            # Fetch email from Gmail API
            email_data = self.gmail.get_message(message_id)
            body = email_data.get("body_plain") or email_data.get("body_html", "")
            subject = email_data.get("subject", "")
            
            if not body:
                logger.warning(f"No email body found for message {message_id}")
                raise ValueError("No email content found")
            
            prompt = self.compose_prompt(subject, body)
            todos_data = self.call_agent(prompt)
            
            return todos_data
            
        except Exception as e:
            logger.error(f"Error extracting todos from message {message_id}: {str(e)}")
            raise

    def _get_user_rules(self) -> Optional[str]:
        try:
            rules_path = Path(__file__).parent / "todo_rules.txt"
            if not rules_path.exists() or rules_path.stat().st_size == 0:
                logger.info("Todo rules file is empty or doesn't exist")
                return None
                
            with open(rules_path, "r") as f:
                rules = f.read().strip()
                
            if not rules:
                logger.info("Todo rules file is empty")
                return None
                
            logger.info("Todo rules loaded successfully")
            return rules
        except Exception as e:
            logger.error(f"Error reading todo rules: {str(e)}")
            return None
    
    def compose_prompt(self, subject: str, email_text: str) -> str:
        base_prompt = f"""Extract all todo items, action items, and tasks from the following email.
        Return a JSON object with the following structure:
        {{
            "todos": [
                {{
                    "task": "The task description",
                    "priority": "high/medium/low",
                    "due_date": "YYYY-MM-DD or null if not specified",
                    "assignee": "Person assigned or null if not clear",
                    "context": "Brief context about the task"
                }}
            ],
            "has_action_required": true/false
        }}
        
        Priority guidelines:
        - high: urgent tasks with explicit deadlines or marked as important
        - medium: tasks with deadlines but not urgent, or standard work items
        - low: nice-to-have items or FYI tasks
        
        Return only valid, parseable JSON. Do not include notes or explanations outside the JSON.
        If no todos are found, return an empty array for "todos" and set "has_action_required" to false.
        """
        
        user_rules = None
        if self.use_memory:
            user_rules = self._get_user_rules()
            
        if user_rules:
            prompt = f"{base_prompt}\n\nUser Rules:\n{user_rules}\n\nEmail Subject: {subject}\n\nEmail Content:\n{email_text}"
        else:
            prompt = f"{base_prompt}\n\nEmail Subject: {subject}\n\nEmail Content:\n{email_text}"
        
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
                
                todos_data = json.loads(content)
                return todos_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                # Return a structured error response
                return {
                    "error": "Failed to parse todo data",
                    "raw_response": response.content,
                    "todos": [],
                    "has_action_required": False
                }
        except Exception as e:
            logger.error(f"Error calling agent: {str(e)}")
            raise
