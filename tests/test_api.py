import pytest
import json
from unittest.mock import patch, MagicMock
from app import db
from app.models import Email

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'stay_backend'

def test_add_user_no_token(client):
    """Test add_user endpoint with no token data"""
    response = client.post('/api/add_user')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'No token data provided' in data['message']

def test_add_user_invalid_token(client):
    """Test add_user endpoint with invalid token"""
    invalid_token = {'invalid': 'token'}
    response = client.post('/api/add_user', json=invalid_token)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Invalid token' in data['message']

@patch('app.utils.auth.GoogleAuthService')
def test_add_user_success(mock_auth_service, client, sample_oauth_token):
    """Test successful add_user endpoint"""
    # Mock the auth service
    mock_instance = mock_auth_service.return_value
    mock_instance.create_credentials_from_token.return_value = MagicMock()
    mock_instance.validate_credentials.return_value = (True, {
        'email': 'test@example.com',
        'messages_total': 100,
        'threads_total': 50
    })
    
    response = client.post('/api/add_user', json=sample_oauth_token)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['user_email'] == 'test@example.com'

def test_get_emails_no_user_email(client):
    """Test get_emails endpoint without user_email parameter"""
    response = client.get('/api/emails')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'user_email parameter required' in data['message']

def test_get_emails_invalid_pagination(client):
    """Test get_emails endpoint with invalid pagination"""
    response = client.get('/api/emails?user_email=test@example.com&limit=invalid')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'valid integers' in data['message']

def test_get_emails_success(client, app, sample_email):
    """Test successful get_emails endpoint"""
    with app.app_context():
        # Create test email
        email = Email(**sample_email)
        email.priority = 'high'
        email.category = 'work'
        email.summary = 'Test summary'
        db.session.add(email)
        db.session.commit()
        
        # Test basic request
        response = client.get('/api/emails?user_email=test@example.com')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(data['emails']) == 1
        assert data['emails'][0]['id'] == sample_email['id']
        
        # Test with filters
        response = client.get('/api/emails?user_email=test@example.com&priority=high')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['emails']) == 1
        
        # Test with non-matching filter
        response = client.get('/api/emails?user_email=test@example.com&priority=low')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['emails']) == 0

def test_get_emails_pagination(client, app):
    """Test get_emails endpoint pagination"""
    with app.app_context():
        # Create multiple test emails
        for i in range(5):
            email = Email(
                id=f'test_email_{i}',
                user_id='test@example.com',
                sender=f'sender{i}@example.com',
                recipient='test@example.com',
                subject=f'Test Subject {i}'
            )
            db.session.add(email)
        db.session.commit()
        
        # Test pagination
        response = client.get('/api/emails?user_email=test@example.com&limit=2&offset=0')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['emails']) == 2
        assert data['pagination']['total'] == 5
        assert data['pagination']['has_next'] is True
        assert data['pagination']['has_prev'] is False

def test_get_email_details_not_found(client):
    """Test get_email_details endpoint with non-existent email"""
    response = client.get('/api/emails/nonexistent')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'Email not found' in data['message']

def test_get_email_details_success(client, app, sample_email):
    """Test successful get_email_details endpoint"""
    with app.app_context():
        email = Email(**sample_email)
        email.summary = 'Detailed test summary'
        db.session.add(email)
        db.session.commit()
        
        response = client.get(f'/api/emails/{sample_email["id"]}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['email']['id'] == sample_email['id']
        assert data['email']['summary'] == 'Detailed test summary'

def test_get_emails_summary(client, app):
    """Test get_emails_summary endpoint"""
    with app.app_context():
        # Create test emails with different categories and priorities
        emails = [
            Email(id='e1', user_id='test@example.com', sender='s1@example.com', 
                 recipient='test@example.com', subject='Work Email', 
                 category='work', priority='high', action_required=True),
            Email(id='e2', user_id='test@example.com', sender='s2@example.com',
                 recipient='test@example.com', subject='Personal Email',
                 category='personal', priority='low', action_required=False),
            Email(id='e3', user_id='test@example.com', sender='s3@example.com',
                 recipient='test@example.com', subject='Promo Email',
                 category='promotional', priority='low', action_required=False)
        ]
        
        db.session.add_all(emails)
        db.session.commit()
        
        response = client.get('/api/emails/summary?user_email=test@example.com')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['summary']['total_emails'] == 3
        assert data['summary']['high_priority'] == 1
        assert data['summary']['action_required'] == 1
        assert 'work' in data['summary']['categories']
        assert data['summary']['categories']['work'] == 1

@patch('app.services.gmail_service.GmailService')
@patch('app.utils.auth.GoogleAuthService')
def test_process_emails_success(mock_auth_service, mock_gmail_service, client, sample_oauth_token, gmail_message_response):
    """Test successful process_emails endpoint"""
    # Mock auth service
    mock_auth_instance = mock_auth_service.return_value
    mock_auth_instance.create_credentials_from_token.return_value = MagicMock()
    mock_auth_instance.get_user_email.return_value = 'test@example.com'
    
    # Mock Gmail service
    mock_gmail_instance = mock_gmail_service.return_value
    mock_gmail_instance.get_recent_messages.return_value = [gmail_message_response]
    
    # Mock LLM service
    with patch('app.services.llm_service.LLMService') as mock_llm:
        mock_llm_instance = mock_llm.return_value
        mock_llm_instance.analyze_email.return_value = {
            'sentiment': 'neutral',
            'priority': 'medium',
            'category': 'work',
            'summary': 'Test analysis',
            'action_required': False
        }
        
        request_data = {
            'oauth_token': sample_oauth_token,
            'days_back': 7,
            'max_emails': 10
        }
        
        response = client.post('/api/process_emails', json=request_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['processed_count'] >= 0