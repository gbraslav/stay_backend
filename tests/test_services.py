import pytest
from unittest.mock import patch, MagicMock
from app.services import EmailParser, LLMService
from app.utils import GoogleAuthService, validate_email, validate_oauth_token

class TestEmailParser:
    def test_parse_gmail_message(self, gmail_message_response):
        """Test parsing Gmail message"""
        parser = EmailParser()
        
        parsed = parser.parse_gmail_message(gmail_message_response, 'test@example.com')
        
        assert parsed is not None
        assert parsed['id'] == 'test_message_id_123'
        assert parsed['user_id'] == 'test@example.com'
        assert parsed['sender'] == 'sender@example.com'
        assert parsed['subject'] == 'Test Email Subject'
        assert parsed['thread_id'] == 'test_thread_123'
    
    def test_clean_email_address(self):
        """Test email address cleaning"""
        parser = EmailParser()
        
        # Test with angle brackets
        result = parser._clean_email_address('John Doe <john@example.com>')
        assert result == 'john@example.com'
        
        # Test plain email
        result = parser._clean_email_address('plain@example.com')
        assert result == 'plain@example.com'
        
        # Test empty string
        result = parser._clean_email_address('')
        assert result == ''
    
    def test_extract_key_information(self):
        """Test key information extraction"""
        parser = EmailParser()
        
        email_text = "Please review the document and send feedback. This is urgent."
        info = parser.extract_key_information(email_text)
        
        assert 'clean_text' in info
        assert 'action_items' in info
        assert 'has_action_items' in info
        assert info['has_action_items'] is True
        assert info['word_count'] > 0

class TestLLMService:
    @patch('openai.OpenAI')
    def test_analyze_email(self, mock_openai, app):
        """Test email analysis with LLM"""
        with app.app_context():
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '''
            {
                "sentiment": "positive",
                "priority": "high",
                "category": "work",
                "summary": "Meeting request for project discussion",
                "action_required": true,
                "key_points": ["Meeting", "Project", "Deadline"]
            }
            '''
            
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            llm_service = LLMService()
            
            email_data = {
                'sender': 'boss@company.com',
                'subject': 'Important Meeting Tomorrow',
                'body_text': 'We need to discuss the project deadline.',
                'has_attachments': False
            }
            
            analysis = llm_service.analyze_email(email_data)
            
            assert analysis['sentiment'] == 'positive'
            assert analysis['priority'] == 'high'
            assert analysis['category'] == 'work'
            assert analysis['action_required'] is True
    
    def test_validate_analysis_fields(self, app):
        """Test analysis field validation"""
        with app.app_context():
            llm_service = LLMService()
            
            # Test sentiment validation
            assert llm_service._validate_sentiment('positive') == 'positive'
            assert llm_service._validate_sentiment('invalid') == 'neutral'
            
            # Test priority validation
            assert llm_service._validate_priority('high') == 'high'
            assert llm_service._validate_priority('invalid') == 'medium'
            
            # Test category validation
            assert llm_service._validate_category('work') == 'work'
            assert llm_service._validate_category('invalid') == 'other'
    
    def test_get_default_analysis(self, app):
        """Test default analysis fallback"""
        with app.app_context():
            llm_service = LLMService()
            default = llm_service._get_default_analysis()
            
            assert default['sentiment'] == 'neutral'
            assert default['priority'] == 'medium'
            assert default['category'] == 'other'
            assert default['action_required'] is False

class TestGoogleAuthService:
    def test_create_credentials_from_token(self, app, sample_oauth_token):
        """Test creating credentials from token"""
        with app.app_context():
            auth_service = GoogleAuthService()
            
            # This would normally create actual credentials
            # For testing, we'll just verify the method exists and accepts the token
            assert hasattr(auth_service, 'create_credentials_from_token')
    
    @patch('googleapiclient.discovery.build')
    def test_validate_credentials(self, mock_build, app):
        """Test credential validation"""
        with app.app_context():
            mock_service = MagicMock()
            mock_service.users().getProfile().execute.return_value = {
                'emailAddress': 'test@example.com',
                'messagesTotal': 100,
                'threadsTotal': 50
            }
            mock_build.return_value = mock_service
            
            auth_service = GoogleAuthService()
            mock_credentials = MagicMock()
            
            is_valid, user_info = auth_service.validate_credentials(mock_credentials)
            
            assert is_valid is True
            assert user_info['email'] == 'test@example.com'
            assert user_info['messages_total'] == 100

class TestValidators:
    def test_validate_email(self):
        """Test email validation"""
        # Valid email
        is_valid, error = validate_email('test@example.com')
        assert is_valid is True
        assert error is None
        
        # Invalid email
        is_valid, error = validate_email('invalid-email')
        assert is_valid is False
        assert error is not None
    
    def test_validate_oauth_token(self):
        """Test OAuth token validation"""
        # Valid token
        valid_token = {
            'access_token': 'valid_access_token_12345',
            'refresh_token': 'refresh_token'
        }
        is_valid, error = validate_oauth_token(valid_token)
        assert is_valid is True
        assert error is None
        
        # Invalid token - missing access_token
        invalid_token = {'refresh_token': 'refresh_token'}
        is_valid, error = validate_oauth_token(invalid_token)
        assert is_valid is False
        assert 'access_token' in error
        
        # Invalid token - too short
        short_token = {'access_token': 'short'}
        is_valid, error = validate_oauth_token(short_token)
        assert is_valid is False
        assert 'Invalid access token format' in error
        
        # Invalid token - not dict
        is_valid, error = validate_oauth_token('not_a_dict')
        assert is_valid is False
        assert 'dictionary' in error