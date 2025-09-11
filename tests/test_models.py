import pytest
from datetime import datetime
from app import db
from app.models import Email

def test_email_model_creation(app, sample_email):
    """Test Email model creation and basic properties"""
    with app.app_context():
        email = Email(**sample_email)
        db.session.add(email)
        db.session.commit()
        
        # Test that email was created
        saved_email = Email.query.get(sample_email['id'])
        assert saved_email is not None
        assert saved_email.sender == sample_email['sender']
        assert saved_email.subject == sample_email['subject']

def test_email_to_dict(app, sample_email):
    """Test Email model to_dict method"""
    with app.app_context():
        email = Email(**sample_email)
        email_dict = email.to_dict()
        
        assert email_dict['id'] == sample_email['id']
        assert email_dict['sender'] == sample_email['sender']
        assert email_dict['subject'] == sample_email['subject']
        assert 'date_received' in email_dict
        assert 'date_processed' in email_dict

def test_email_to_summary_dict(app, sample_email):
    """Test Email model to_summary_dict method"""
    with app.app_context():
        email = Email(**sample_email)
        summary_dict = email.to_summary_dict()
        
        # Summary should contain fewer fields
        expected_fields = [
            'id', 'sender', 'subject', 'date_received',
            'priority', 'category', 'summary', 'action_required',
            'has_attachments'
        ]
        
        for field in expected_fields:
            assert field in summary_dict

def test_email_with_analysis(app, sample_email):
    """Test Email model with LLM analysis data"""
    with app.app_context():
        # Add analysis data
        sample_email.update({
            'sentiment': 'neutral',
            'priority': 'medium',
            'category': 'work',
            'summary': 'Test email summary',
            'action_required': True
        })
        
        email = Email(**sample_email)
        db.session.add(email)
        db.session.commit()
        
        saved_email = Email.query.get(sample_email['id'])
        assert saved_email.sentiment == 'neutral'
        assert saved_email.priority == 'medium'
        assert saved_email.category == 'work'
        assert saved_email.action_required is True

def test_email_date_handling(app, sample_email):
    """Test Email model date handling"""
    with app.app_context():
        test_date = datetime(2024, 9, 11, 10, 0, 0)
        sample_email['date_received'] = test_date
        
        email = Email(**sample_email)
        db.session.add(email)
        db.session.commit()
        
        saved_email = Email.query.get(sample_email['id'])
        assert saved_email.date_received == test_date
        assert saved_email.date_processed is not None

def test_email_query_filtering(app):
    """Test Email model query filtering"""
    with app.app_context():
        # Create test emails
        email1 = Email(
            id='email1',
            user_id='user1@example.com',
            sender='sender1@example.com',
            recipient='user1@example.com',
            subject='Important Meeting',
            priority='high',
            category='work',
            action_required=True
        )
        
        email2 = Email(
            id='email2',
            user_id='user1@example.com',
            sender='sender2@example.com',
            recipient='user1@example.com',
            subject='Newsletter',
            priority='low',
            category='promotional',
            action_required=False
        )
        
        db.session.add_all([email1, email2])
        db.session.commit()
        
        # Test filtering by priority
        high_priority = Email.query.filter_by(priority='high').all()
        assert len(high_priority) == 1
        assert high_priority[0].id == 'email1'
        
        # Test filtering by action_required
        action_emails = Email.query.filter_by(action_required=True).all()
        assert len(action_emails) == 1
        assert action_emails[0].id == 'email1'
        
        # Test filtering by category
        work_emails = Email.query.filter_by(category='work').all()
        assert len(work_emails) == 1
        assert work_emails[0].subject == 'Important Meeting'