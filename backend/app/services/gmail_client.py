"""
Gmail Client Service

Handles all interactions with the Gmail API, providing a clean interface for routes
to use without dealing with the underlying API complexities.
"""
import os
import base64
from typing import Dict, List, Optional, Any, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from app.core.auth import load_token, refresh_access_token, save_token, SCOPES

logger = logging.getLogger(__name__)

class GmailClient:
    """
    Client for interacting with Gmail API.
    
    This class centralizes all Gmail operations and provides a clean interface
    for the rest of the application to use.
    """
    
    def __init__(self):
        """Initialize the Gmail client."""
        self.service = None
        self.user_id = 'me'  # Default user ID for Gmail API
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using stored credentials.
        
        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        try:
            token_data = load_token()
            if not token_data:
                logger.error("No token data found")
                return False
                
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            
            # Refresh token if expired
            if creds.expired and creds.refresh_token:
                new_token_data = refresh_access_token(creds.refresh_token)
                # Update access token in credentials
                creds.token = new_token_data['access_token']
                # Save updated token
                token_data.update(new_token_data)
                save_token(token_data)
            
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_messages(self, max_results: int = 10, query: str = "") -> List[Dict]:
        """
        Get messages from Gmail.
        
        Args:
            max_results: Maximum number of messages to return
            query: Gmail search query
            
        Returns:
            List of message dictionaries
        """
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Gmail")
        
        try:
            # Get message IDs
            results = self.service.users().messages().list(
                userId=self.user_id, 
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full message data for each ID
            full_messages = []
            for msg in messages:
                msg_data = self.get_message(msg['id'])
                if msg_data:
                    full_messages.append(msg_data)
            
            return full_messages
        except HttpError as error:
            logger.error(f"Error retrieving messages: {error}")
            raise
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: The ID of the message to retrieve
            
        Returns:
            Message dictionary or None if not found
        """
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Gmail")
        
        try:
            message = self.service.users().messages().get(
                userId=self.user_id, 
                id=message_id,
                format='full'
            ).execute()
            
            # Process the message to extract headers, body, etc.
            processed_message = self._process_message(message)
            return processed_message
        except HttpError as error:
            logger.error(f"Error retrieving message {message_id}: {error}")
            return None
    
    def _process_message(self, message: Dict) -> Dict:
        """
        Process a raw message from Gmail API into a more usable format.
        
        Args:
            message: Raw message from Gmail API
            
        Returns:
            Processed message with headers and body extracted
        """
        headers = {}
        for header in message['payload']['headers']:
            headers[header['name'].lower()] = header['value']
        
        # Extract plain text and HTML content
        plain_content, html_content = self._extract_content(message['payload'])
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'label_ids': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'headers': headers,
            'subject': headers.get('subject', ''),
            'from': headers.get('from', ''),
            'to': headers.get('to', ''),
            'date': headers.get('date', ''),
            'body_plain': plain_content,
            'body_html': html_content,
            'raw': message  # Include raw message for advanced processing if needed
        }
    
    def _extract_content(self, payload: Dict) -> Tuple[str, str]:
        """
        Extract plain text and HTML content from message payload.
        
        Args:
            payload: Message payload from Gmail API
            
        Returns:
            Tuple of (plain_text, html_content)
        """
        plain_content = ""
        html_content = ""
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    plain_content = self._decode_body(part['body'].get('data', ''))
                elif part['mimeType'] == 'text/html':
                    html_content = self._decode_body(part['body'].get('data', ''))
                # Recursively process nested multipart messages
                elif 'parts' in part:
                    nested_plain, nested_html = self._extract_content(part)
                    if nested_plain and not plain_content:
                        plain_content = nested_plain
                    if nested_html and not html_content:
                        html_content = nested_html
        # Handle single part messages
        elif payload.get('mimeType') == 'text/plain':
            plain_content = self._decode_body(payload['body'].get('data', ''))
        elif payload.get('mimeType') == 'text/html':
            html_content = self._decode_body(payload['body'].get('data', ''))
        
        return plain_content, html_content
    
    def _decode_body(self, data: str) -> str:
        """
        Decode base64 encoded message body.
        
        Args:
            data: Base64 encoded string
            
        Returns:
            Decoded string
        """
        if not data:
            return ""
        
        # Add padding if needed
        padded_data = data.replace('-', '+').replace('_', '/')
        padding_needed = len(padded_data) % 4
        if padding_needed:
            padded_data += '=' * (4 - padding_needed)
        
        try:
            return base64.b64decode(padded_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error decoding message body: {e}")
            return ""
    
    def send_message(self, to: str, subject: str, body_plain: str, body_html: str = None, 
                     cc: str = None, bcc: str = None, thread_id: str = None) -> Optional[str]:
        """
        Send an email message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body_plain: Plain text body
            body_html: HTML body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            thread_id: Thread ID to reply to (optional)
            
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Gmail")
        
        try:
            message = MIMEMultipart('alternative')
            message['To'] = to
            message['Subject'] = subject
            
            if cc:
                message['Cc'] = cc
            if bcc:
                message['Bcc'] = bcc
            
            # Add plain text part
            part1 = MIMEText(body_plain, 'plain')
            message.attach(part1)
            
            # Add HTML part if provided
            if body_html:
                part2 = MIMEText(body_html, 'html')
                message.attach(part2)
            
            # Encode the message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create the message dict
            message_dict = {
                'raw': encoded_message
            }
            
            # Add thread ID if replying to a thread
            if thread_id:
                message_dict['threadId'] = thread_id
            
            # Send the message
            sent_message = self.service.users().messages().send(
                userId=self.user_id, 
                body=message_dict
            ).execute()
            
            return sent_message['id']
        except HttpError as error:
            logger.error(f"Error sending message: {error}")
            return None
    
    def reply_to_message(self, message_id: str, body_plain: str, body_html: str = None) -> Optional[str]:
        """
        Reply to a specific message.
        
        Args:
            message_id: ID of the message to reply to
            body_plain: Plain text body
            body_html: HTML body (optional)
            
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Gmail")
        
        try:
            # Get the original message to extract headers
            original = self.get_message(message_id)
            if not original:
                return None
            
            # Extract necessary information
            to_address = original['headers'].get('from', '')
            subject = original['headers'].get('subject', '')
            if not subject.startswith('Re:'):
                subject = f"Re: {subject}"
            
            # Send the reply
            return self.send_message(
                to=to_address,
                subject=subject,
                body_plain=body_plain,
                body_html=body_html,
                thread_id=original['thread_id']
            )
        except HttpError as error:
            logger.error(f"Error replying to message {message_id}: {error}")
            return None
    
    def get_labels(self) -> List[Dict]:
        """
        Get all labels from Gmail.
        
        Returns:
            List of label dictionaries
        """
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Gmail")
        
        try:
            results = self.service.users().labels().list(userId=self.user_id).execute()
            return results.get('labels', [])
        except HttpError as error:
            logger.error(f"Error retrieving labels: {error}")
            return []
    
    def add_label_to_message(self, message_id: str, label_id: str) -> bool:
        """
        Add a label to a message.
        
        Args:
            message_id: ID of the message
            label_id: ID of the label to add
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Gmail")
        
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"Error adding label {label_id} to message {message_id}: {error}")
            return False
    
    def remove_label_from_message(self, message_id: str, label_id: str) -> bool:
        """
        Remove a label from a message.
        
        Args:
            message_id: ID of the message
            label_id: ID of the label to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Gmail")
        
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={'removeLabelIds': [label_id]}
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"Error removing label {label_id} from message {message_id}: {error}")
            return False
