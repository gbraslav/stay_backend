import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class GoogleAuthService:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        self.client_id = current_app.config['GOOGLE_CLIENT_ID']
        self.client_secret = current_app.config['GOOGLE_CLIENT_SECRET']
        
    def create_credentials_from_token(self, token_data):
        """
        Create Google credentials from OAuth token data received from client
        
        Args:
            token_data (dict): OAuth token information from client
            
        Returns:
            Credentials: Google credentials object
        """
        try:
            if isinstance(token_data, str):
                token_data = json.loads(token_data)
                
            credentials = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.SCOPES
            )
            
            # Refresh token if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
            return credentials
            
        except Exception as e:
            logger.error(f"Error creating credentials: {str(e)}")
            raise ValueError(f"Invalid token data: {str(e)}")
    
    def validate_credentials(self, credentials):
        """
        Validate credentials by making a test API call
        
        Args:
            credentials: Google credentials object
            
        Returns:
            tuple: (is_valid, user_info)
        """
        try:
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            
            return True, {
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0)
            }
            
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return False, None
    
    def get_user_email(self, credentials):
        """
        Get user's email address from credentials
        
        Args:
            credentials: Google credentials object
            
        Returns:
            str: User's email address or None
        """
        try:
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception as e:
            logger.error(f"Error getting user email: {str(e)}")
            return None