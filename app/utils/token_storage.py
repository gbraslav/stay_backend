"""
In-memory token storage for user OAuth tokens
"""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import threading

class TokenStorage:
    """Thread-safe in-memory storage for user OAuth tokens"""
    
    def __init__(self):
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def store_token(self, user_email: str, token_data: Dict[str, Any]) -> None:
        """Store token data for a user"""
        with self._lock:
            # Calculate expiry time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self._tokens[user_email] = {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'scope': token_data.get('scope'),
                'expires_at': expires_at,
                'stored_at': datetime.now()
            }
    
    def get_token(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Get token data for a user"""
        with self._lock:
            return self._tokens.get(user_email)
    
    def is_token_valid(self, user_email: str) -> bool:
        """Check if stored token is still valid"""
        token_data = self.get_token(user_email)
        if not token_data:
            return False
        
        # Check if token has expired (with 5 minute buffer)
        expires_at = token_data.get('expires_at')
        if expires_at and datetime.now() > expires_at - timedelta(minutes=5):
            return False
        
        return True
    
    def remove_token(self, user_email: str) -> None:
        """Remove token data for a user"""
        with self._lock:
            self._tokens.pop(user_email, None)
    
    def get_stored_users(self) -> list:
        """Get list of users with stored tokens"""
        with self._lock:
            return list(self._tokens.keys())
    
    def clear_all(self) -> None:
        """Clear all stored tokens"""
        with self._lock:
            self._tokens.clear()

# Global instance
token_storage = TokenStorage()