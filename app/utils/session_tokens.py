"""
Session token management for user authentication
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, Tuple
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class SessionTokenService:
    """Service for managing JWT-based session tokens"""

    def __init__(self):
        self.algorithm = 'HS256'

    def _get_secret_key(self) -> str:
        """Get JWT secret key from config"""
        secret = current_app.config.get('JWT_SECRET_KEY')
        if not secret:
            raise ValueError("JWT_SECRET_KEY not configured")
        return secret

    def generate_session_token(self, user_email: str, expires_in: int = 3600) -> str:
        """
        Generate a time-based session token for a user

        Args:
            user_email (str): User's email address
            expires_in (int): Token expiration time in seconds (default: 1 hour)

        Returns:
            str: JWT token string
        """
        try:
            now = datetime.now(timezone.utc)
            expiry = now + timedelta(seconds=expires_in)

            payload = {
                'user_email': user_email,
                'iat': now,  # Issued at
                'exp': expiry,  # Expires at
                'type': 'session'
            }

            token = jwt.encode(
                payload,
                self._get_secret_key(),
                algorithm=self.algorithm
            )

            logger.info(f"Generated session token for user: {user_email}, expires: {expiry}")
            return token

        except Exception as e:
            logger.error(f"Error generating session token: {str(e)}")
            raise ValueError(f"Failed to generate session token: {str(e)}")

    def validate_session_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a session token and return user information

        Args:
            token (str): JWT token to validate

        Returns:
            tuple: (is_valid, payload_dict)
        """
        try:
            payload = jwt.decode(
                token,
                self._get_secret_key(),
                algorithms=[self.algorithm]
            )

            # Verify token type
            if payload.get('type') != 'session':
                logger.warning("Invalid token type")
                return False, None

            # Token is valid and not expired (jwt.decode handles expiration)
            return True, payload

        except jwt.ExpiredSignatureError:
            logger.warning("Session token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid session token: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error validating session token: {str(e)}")
            return False, None

    def decode_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode session token without validation (for inspection)

        Args:
            token (str): JWT token to decode

        Returns:
            dict: Token payload or None if invalid
        """
        try:
            # Decode without verification for inspection
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except Exception as e:
            logger.error(f"Error decoding session token: {str(e)}")
            return None

    def get_user_from_token(self, token: str) -> Optional[str]:
        """
        Extract user email from a valid session token

        Args:
            token (str): JWT token

        Returns:
            str: User email or None if invalid
        """
        is_valid, payload = self.validate_session_token(token)
        if is_valid and payload:
            return payload.get('user_email')
        return None

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get expiration time from token

        Args:
            token (str): JWT token

        Returns:
            datetime: Expiration time or None if invalid
        """
        payload = self.decode_session_token(token)
        if payload and 'exp' in payload:
            return datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired

        Args:
            token (str): JWT token

        Returns:
            bool: True if expired, False if valid
        """
        expiry = self.get_token_expiry(token)
        if expiry:
            return datetime.now(timezone.utc) > expiry
        return True  # Assume expired if can't determine


# Global instance
session_token_service = SessionTokenService()