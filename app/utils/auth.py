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
                
            # For access-token-only scenarios, only provide essential fields
            if token_data.get('refresh_token'):
                # Full credentials with refresh capability
                credentials = Credentials(
                    token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=self.SCOPES
                )
            else:
                # Access-token-only credentials (no refresh capability)
                # Include minimal required fields to prevent refresh attempts
                credentials = Credentials(
                    token=token_data.get('access_token'),
                    refresh_token=None,  # Explicitly set to None
                    token_uri=None,      # No refresh URI
                    client_id=None,      # No client info
                    client_secret=None,
                    scopes=self.SCOPES
                )
            
            # Refresh token if needed (only if refresh token is available)
            if credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {str(e)}")
                    # Continue with expired token - validation will catch this
                
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
            # For access-token-only credentials, we can't refresh expired tokens
            # so we just attempt the API call directly
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()

            return True, {
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0)
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Credential validation failed: {error_msg}")

            # Provide more specific error messages for common issues
            if "refresh the access token" in error_msg:
                logger.info("Access token may be expired and no refresh token available")
            elif "invalid_token" in error_msg.lower():
                logger.info("Access token is invalid or malformed")

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

    def create_credentials_from_refresh_token(self, refresh_token: str):
        """
        Create Google credentials from refresh token only

        Args:
            refresh_token (str): Refresh token string

        Returns:
            Credentials: Google credentials object
        """
        try:
            credentials = Credentials(
                token=None,  # No initial access token
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.SCOPES
            )

            # Force refresh to get fresh access token
            credentials.refresh(Request())

            return credentials

        except Exception as e:
            logger.error(f"Error creating credentials from refresh token: {str(e)}")
            raise ValueError(f"Invalid refresh token: {str(e)}")

    def refresh_access_token(self, refresh_token: str):
        """
        Get fresh access token from refresh token

        Args:
            refresh_token (str): Refresh token string

        Returns:
            dict: Token information including access_token and expires_in
        """
        try:
            credentials = self.create_credentials_from_refresh_token(refresh_token)

            # Extract token information
            token_info = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600,  # Google tokens typically expire in 1 hour
                'scope': ' '.join(credentials.scopes) if credentials.scopes else None
            }

            return token_info

        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            raise ValueError(f"Failed to refresh access token: {str(e)}")