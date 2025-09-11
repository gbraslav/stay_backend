import pytest
import os
from app import create_app, db
from app.models import Email
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    GOOGLE_CLIENT_ID = 'test-client-id'
    GOOGLE_CLIENT_SECRET = 'test-client-secret'
    OPENAI_API_KEY = 'test-openai-key'
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'

@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def sample_email():
    return {
        'id': 'test_message_id_123',
        'user_id': 'test@example.com',
        'sender': 'sender@example.com',
        'recipient': 'test@example.com',
        'subject': 'Test Email Subject',
        'body_text': 'This is a test email body content.',
        'body_html': '<p>This is a test email body content.</p>',
        'thread_id': 'test_thread_123',
        'labels': 'INBOX,UNREAD',
        'has_attachments': False,
        'attachment_count': 0
    }

@pytest.fixture
def sample_oauth_token():
    return {
        'access_token': 'test_access_token_12345',
        'refresh_token': 'test_refresh_token_67890',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': 'https://www.googleapis.com/auth/gmail.readonly'
    }

@pytest.fixture
def gmail_message_response():
    """Sample Gmail API message response"""
    return {
        'id': 'test_message_id_123',
        'threadId': 'test_thread_123',
        'labelIds': ['INBOX', 'UNREAD'],
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'Test Sender <sender@example.com>'},
                {'name': 'To', 'value': 'test@example.com'},
                {'name': 'Subject', 'value': 'Test Email Subject'},
                {'name': 'Date', 'value': 'Wed, 11 Sep 2024 10:00:00 +0000'}
            ],
            'body': {
                'data': 'VGhpcyBpcyBhIHRlc3QgZW1haWwgYm9keSBjb250ZW50Lg=='  # base64 encoded
            },
            'mimeType': 'text/plain'
        }
    }