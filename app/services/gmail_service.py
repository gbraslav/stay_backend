import base64
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self, credentials):
        self.service = build('gmail', 'v1', credentials=credentials)
        self.credentials = credentials
    
    def get_messages(self, query='', max_results=50, page_token=None):
        """
        Get list of messages based on query
        
        Args:
            query (str): Gmail search query
            max_results (int): Maximum number of messages to return
            page_token (str): Token for pagination
            
        Returns:
            dict: Messages list with pagination info
        """
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                pageToken=page_token
            ).execute()
            
            messages = result.get('messages', [])
            next_page_token = result.get('nextPageToken')
            
            return {
                'messages': messages,
                'next_page_token': next_page_token,
                'total_estimated': result.get('resultSizeEstimate', 0)
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error in get_messages: {e}")
            raise
    
    def get_message_details(self, message_id):
        """
        Get full details of a specific message
        
        Args:
            message_id (str): Gmail message ID
            
        Returns:
            dict: Full message details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return message
            
        except HttpError as e:
            logger.error(f"Gmail API error in get_message_details: {e}")
            raise
    
    def get_recent_messages(self, days=7, max_results=100, query=None):
        """
        Get recent messages from the last N days
        
        Args:
            days (int): Number of days to look back
            max_results (int): Maximum number of messages
            query (str, optional): Additional Gmail search query
            
        Returns:
            list: List of message details
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Format dates for Gmail query
            date_query = f"after:{start_date.strftime('%Y/%m/%d')} before:{end_date.strftime('%Y/%m/%d')}"
            
            # Combine with user query if provided
            if query and query.strip():
                combined_query = f"{date_query} {query.strip()}"
            else:
                combined_query = date_query
            
            # Get message list
            messages_result = self.get_messages(query=combined_query, max_results=max_results)
            messages = messages_result.get('messages', [])
            
            # Get details for each message
            detailed_messages = []
            for message in messages[:max_results]:  # Limit to avoid rate limits
                try:
                    details = self.get_message_details(message['id'])
                    detailed_messages.append(details)
                except Exception as e:
                    logger.warning(f"Failed to get details for message {message['id']}: {e}")
                    continue
            
            return detailed_messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            raise
    
    def decode_message_part(self, part):
        """
        Decode message part (body content)
        
        Args:
            part (dict): Message part from Gmail API
            
        Returns:
            str: Decoded content
        """
        try:
            data = part.get('body', {}).get('data')
            if not data:
                return ''
            
            # Decode base64url
            decoded_data = base64.urlsafe_b64decode(data + '===')
            return decoded_data.decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.warning(f"Error decoding message part: {e}")
            return ''
    
    def extract_headers(self, message):
        """
        Extract important headers from message
        
        Args:
            message (dict): Gmail message object
            
        Returns:
            dict: Extracted headers
        """
        headers = {}
        payload = message.get('payload', {})
        
        for header in payload.get('headers', []):
            name = header.get('name', '').lower()
            value = header.get('value', '')
            
            if name in ['from', 'to', 'subject', 'date', 'cc', 'bcc']:
                headers[name] = value
        
        return headers
    
    def get_message_body(self, message):
        """
        Extract body content from message
        
        Args:
            message (dict): Gmail message object
            
        Returns:
            dict: Body content (text and html)
        """
        payload = message.get('payload', {})
        body = {'text': '', 'html': ''}
        
        def extract_parts(parts):
            for part in parts:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    body['text'] += self.decode_message_part(part)
                elif mime_type == 'text/html':
                    body['html'] += self.decode_message_part(part)
                elif 'parts' in part:
                    extract_parts(part['parts'])
        
        # Handle single part message
        if 'parts' not in payload:
            mime_type = payload.get('mimeType', '')
            if mime_type == 'text/plain':
                body['text'] = self.decode_message_part(payload)
            elif mime_type == 'text/html':
                body['html'] = self.decode_message_part(payload)
        else:
            extract_parts(payload['parts'])
        
        return body
    
    def check_connection(self):
        """
        Check if the Gmail connection is working
        
        Returns:
            bool: True if connection is valid
        """
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return True
        except Exception as e:
            logger.error(f"Gmail connection check failed: {e}")
            return False