import re
from datetime import datetime
from email.utils import parsedate_to_datetime
import html2text
import logging

logger = logging.getLogger(__name__)

class EmailParser:
    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0
    
    def parse_gmail_message(self, message, user_id):
        """
        Parse Gmail message into structured data
        
        Args:
            message (dict): Raw Gmail message from API
            user_id (str): User identifier
            
        Returns:
            dict: Parsed email data
        """
        try:
            # Extract headers
            headers = self._extract_headers(message)
            
            # Extract body content
            body_data = self._extract_body(message)
            
            # Parse date
            date_received = self._parse_date(headers.get('date'))
            
            # Extract metadata
            metadata = self._extract_metadata(message)
            
            return {
                'id': message.get('id'),
                'user_id': user_id,
                'sender': self._clean_email_address(headers.get('from', '')),
                'recipient': headers.get('to', ''),
                'subject': headers.get('subject', ''),
                'body_text': body_data.get('text', ''),
                'body_html': body_data.get('html', ''),
                'date_received': date_received,
                'thread_id': message.get('threadId'),
                'labels': ','.join(message.get('labelIds', [])),
                'has_attachments': metadata.get('has_attachments', False),
                'attachment_count': metadata.get('attachment_count', 0)
            }
            
        except Exception as e:
            logger.error(f"Error parsing message {message.get('id', 'unknown')}: {e}")
            return None
    
    def _extract_headers(self, message):
        """Extract headers from Gmail message"""
        headers = {}
        payload = message.get('payload', {})
        
        for header in payload.get('headers', []):
            name = header.get('name', '').lower()
            value = header.get('value', '')
            headers[name] = value
        
        return headers
    
    def _extract_body(self, message):
        """Extract body content from Gmail message"""
        payload = message.get('payload', {})
        body = {'text': '', 'html': ''}
        
        def process_parts(parts):
            for part in parts:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    body['text'] += self._decode_body_data(part.get('body', {}))
                elif mime_type == 'text/html':
                    body['html'] += self._decode_body_data(part.get('body', {}))
                elif 'parts' in part:
                    process_parts(part['parts'])
        
        # Handle single part message
        if 'parts' not in payload:
            mime_type = payload.get('mimeType', '')
            body_data = payload.get('body', {})
            
            if mime_type == 'text/plain':
                body['text'] = self._decode_body_data(body_data)
            elif mime_type == 'text/html':
                body['html'] = self._decode_body_data(body_data)
        else:
            process_parts(payload['parts'])
        
        # Convert HTML to text if no plain text available
        if not body['text'] and body['html']:
            body['text'] = self.html_converter.handle(body['html'])
        
        return body
    
    def _decode_body_data(self, body_data):
        """Decode base64 body data"""
        try:
            import base64
            data = body_data.get('data', '')
            if data:
                decoded_data = base64.urlsafe_b64decode(data + '===')
                return decoded_data.decode('utf-8', errors='ignore')
            return ''
        except Exception as e:
            logger.warning(f"Error decoding body data: {e}")
            return ''
    
    def _parse_date(self, date_string):
        """Parse email date string to datetime"""
        if not date_string:
            return datetime.utcnow()
        
        try:
            return parsedate_to_datetime(date_string)
        except Exception as e:
            logger.warning(f"Error parsing date '{date_string}': {e}")
            return datetime.utcnow()
    
    def _clean_email_address(self, email_string):
        """Extract clean email address from string like 'Name <email@domain.com>'"""
        if not email_string:
            return ''
        
        # Look for email in angle brackets first
        match = re.search(r'<([^>]+)>', email_string)
        if match:
            return match.group(1).strip()
        
        # Look for just email pattern
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email_string)
        if match:
            return match.group(0)
        
        return email_string.strip()
    
    def _extract_metadata(self, message):
        """Extract metadata like attachments"""
        payload = message.get('payload', {})
        attachment_count = 0
        has_attachments = False
        
        def count_attachments(parts):
            nonlocal attachment_count, has_attachments
            for part in parts:
                if part.get('filename'):
                    attachment_count += 1
                    has_attachments = True
                elif 'parts' in part:
                    count_attachments(part['parts'])
        
        if 'parts' in payload:
            count_attachments(payload['parts'])
        elif payload.get('filename'):
            attachment_count = 1
            has_attachments = True
        
        return {
            'has_attachments': has_attachments,
            'attachment_count': attachment_count
        }
    
    def extract_key_information(self, email_text):
        """
        Extract key information from email text for LLM processing
        
        Args:
            email_text (str): Email body text
            
        Returns:
            dict: Key information extracted
        """
        # Remove excessive whitespace
        clean_text = re.sub(r'\s+', ' ', email_text.strip())
        
        # Extract potential action items (basic patterns)
        action_patterns = [
            r'please\s+([^.!?]+)',
            r'could\s+you\s+([^.!?]+)',
            r'need\s+to\s+([^.!?]+)',
            r'action\s+required[:\s]*([^.!?]+)',
            r'urgent[:\s]*([^.!?]+)'
        ]
        
        action_items = []
        for pattern in action_patterns:
            matches = re.finditer(pattern, clean_text, re.IGNORECASE)
            for match in matches:
                action_items.append(match.group(1).strip())
        
        return {
            'clean_text': clean_text[:5000],  # Limit for LLM processing
            'action_items': action_items,
            'has_action_items': len(action_items) > 0,
            'word_count': len(clean_text.split()),
            'char_count': len(clean_text)
        }