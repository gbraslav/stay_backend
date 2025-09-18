"""
Startup utilities for restoring user sessions from persistent storage
"""
import logging
from typing import Dict, List
from flask import current_app
from app.utils.file_token_storage import FileTokenStorage
from app.utils.token_storage import token_storage
from app.utils.session_tokens import session_token_service
from app.utils.auth import GoogleAuthService

logger = logging.getLogger(__name__)


def restore_user_sessions():
    """
    Restore user sessions from persistent storage on app startup

    This function:
    1. Loads persisted refresh tokens from file
    2. Uses refresh tokens to get fresh access tokens
    3. Generates new session tokens
    4. Stores everything in memory for immediate use
    """
    try:
        # Get file storage path from config
        storage_path = current_app.config.get('TOKEN_STORAGE_FILE', 'user_tokens.json')
        file_storage = FileTokenStorage(storage_path)

        # Get list of users with stored tokens
        stored_users = file_storage.get_stored_users()

        if not stored_users:
            logger.info("No persisted users found")
            return

        logger.info(f"Found {len(stored_users)} persisted users, restoring sessions...")

        auth_service = GoogleAuthService()
        restored_count = 0
        failed_count = 0

        for user_email in stored_users:
            try:
                # Get stored token data
                stored_data = file_storage.get_token(user_email)
                if not stored_data:
                    logger.warning(f"No token data found for user: {user_email}")
                    continue

                refresh_token = stored_data.get('refresh_token')
                if not refresh_token:
                    logger.warning(f"No refresh token found for user: {user_email}")
                    continue

                # Use refresh token to get fresh access token
                logger.debug(f"Refreshing access token for user: {user_email}")
                credentials = auth_service.create_credentials_from_refresh_token(refresh_token)

                # Generate new session token (1 hour expiry)
                session_expires_in = 3600
                session_token = session_token_service.generate_session_token(
                    user_email,
                    expires_in=session_expires_in
                )

                # Store in memory for immediate use
                session_token_data = {
                    'access_token': credentials.token,
                    'refresh_token': refresh_token,
                    'token_type': 'Bearer',
                    'expires_in': session_expires_in,
                    'scope': 'https://www.googleapis.com/auth/gmail.readonly',
                    'session_token': session_token
                }
                token_storage.store_token(user_email, session_token_data)

                logger.info(f"✅ Restored session for user: {user_email}")
                restored_count += 1

            except Exception as e:
                logger.error(f"❌ Failed to restore session for user {user_email}: {str(e)}")
                failed_count += 1
                continue

        logger.info(f"Session restoration complete: {restored_count} successful, {failed_count} failed")

    except Exception as e:
        logger.error(f"Error during session restoration: {str(e)}")


def get_session_stats() -> Dict:
    """
    Get statistics about current sessions

    Returns:
        dict: Session statistics
    """
    try:
        stored_users = token_storage.get_stored_users()

        stats = {
            'total_sessions': len(stored_users),
            'users': stored_users
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        return {'total_sessions': 0, 'users': []}