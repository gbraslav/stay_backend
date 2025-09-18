"""
File-based token storage for user OAuth tokens with persistence
"""
import json
import os
import threading
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import fcntl
from pathlib import Path


class FileTokenStorage:
    """Thread-safe file-based storage for user OAuth tokens"""

    def __init__(self, storage_path: str = "user_tokens.json"):
        self.storage_path = Path(storage_path)
        self._lock = threading.Lock()
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._load_from_file()

    def _load_from_file(self) -> None:
        """Load tokens from file into memory cache"""
        if not self.storage_path.exists():
            self._memory_cache = {}
            return

        try:
            with open(self.storage_path, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                data = json.load(f)

                # Convert datetime strings back to datetime objects
                for user_email, token_data in data.items():
                    if 'expires_at' in token_data:
                        token_data['expires_at'] = datetime.fromisoformat(token_data['expires_at'])
                    if 'stored_at' in token_data:
                        token_data['stored_at'] = datetime.fromisoformat(token_data['stored_at'])

                self._memory_cache = data
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            # If file is corrupted or missing, start fresh
            self._memory_cache = {}

    def _save_to_file(self) -> None:
        """Save memory cache to file"""
        # Prepare data for JSON serialization
        data_to_save = {}
        for user_email, token_data in self._memory_cache.items():
            serializable_data = token_data.copy()
            if 'expires_at' in serializable_data and isinstance(serializable_data['expires_at'], datetime):
                serializable_data['expires_at'] = serializable_data['expires_at'].isoformat()
            if 'stored_at' in serializable_data and isinstance(serializable_data['stored_at'], datetime):
                serializable_data['stored_at'] = serializable_data['stored_at'].isoformat()
            data_to_save[user_email] = serializable_data

        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first, then rename for atomicity
        temp_path = self.storage_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                json.dump(data_to_save, f, indent=2)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Atomic move
            temp_path.rename(self.storage_path)

            # Set restrictive permissions (owner read/write only)
            os.chmod(self.storage_path, 0o600)

        except Exception as e:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                temp_path.unlink()
            raise e

    def store_token(self, user_email: str, token_data: Dict[str, Any]) -> None:
        """Store token data for a user"""
        with self._lock:
            # Calculate expiry time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)

            self._memory_cache[user_email] = {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'scope': token_data.get('scope'),
                'expires_at': expires_at,
                'stored_at': datetime.now()
            }

            # Persist to file
            self._save_to_file()

    def get_token(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Get token data for a user"""
        with self._lock:
            return self._memory_cache.get(user_email)

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
            if user_email in self._memory_cache:
                del self._memory_cache[user_email]
                self._save_to_file()

    def get_stored_users(self) -> list:
        """Get list of users with stored tokens"""
        with self._lock:
            return list(self._memory_cache.keys())

    def clear_all(self) -> None:
        """Clear all stored tokens"""
        with self._lock:
            self._memory_cache.clear()
            self._save_to_file()

    def refresh_from_file(self) -> None:
        """Reload tokens from file (useful for external changes)"""
        with self._lock:
            self._load_from_file()