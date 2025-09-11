from app import create_app
from app.models import Email
from app.services import GmailService, EmailParser, LLMService
from app.utils import GoogleAuthService
from app import db
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# Create Flask app
app = create_app()

# Create Celery instance
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task
def process_user_emails_task(oauth_token, user_email, days_back=7, max_emails=50):
    """
    Background task to process user emails
    
    Args:
        oauth_token (dict): User's OAuth token
        user_email (str): User's email address
        days_back (int): Days to look back for emails
        max_emails (int): Maximum emails to process
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Starting email processing task for user: {user_email}")
        
        # Create services
        auth_service = GoogleAuthService()
        credentials = auth_service.create_credentials_from_token(oauth_token)
        
        gmail_service = GmailService(credentials)
        email_parser = EmailParser()
        llm_service = LLMService()
        
        # Fetch recent messages
        messages = gmail_service.get_recent_messages(days=days_back, max_results=max_emails)
        
        processed_count = 0
        errors = []
        
        for message in messages:
            try:
                # Parse email
                parsed_email = email_parser.parse_gmail_message(message, user_email)
                if not parsed_email:
                    continue
                
                # Check if email already exists
                existing_email = Email.query.get(parsed_email['id'])
                if existing_email:
                    logger.info(f"Email {parsed_email['id']} already exists, skipping")
                    continue
                
                # Analyze with LLM
                analysis = llm_service.analyze_email(parsed_email)
                
                # Combine parsed data with analysis
                email_data = {**parsed_email, **analysis}
                
                # Create Email object
                email_obj = Email(**email_data)
                db.session.add(email_obj)
                
                processed_count += 1
                
                # Commit in batches to avoid memory issues
                if processed_count % 10 == 0:
                    db.session.commit()
                    logger.info(f"Committed batch: {processed_count} emails processed")
                
            except Exception as e:
                logger.warning(f"Error processing message {message.get('id', 'unknown')}: {e}")
                errors.append(f"Message {message.get('id', 'unknown')}: {str(e)}")
        
        # Final commit
        try:
            db.session.commit()
            logger.info(f"Email processing task completed for {user_email}: {processed_count} emails processed")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database commit error: {e}")
            raise
        
        return {
            'status': 'success',
            'user_email': user_email,
            'processed_count': processed_count,
            'total_fetched': len(messages),
            'errors_count': len(errors),
            'errors': errors[:10]  # Limit error details
        }
        
    except Exception as e:
        logger.error(f"Email processing task failed for {user_email}: {str(e)}")
        db.session.rollback()
        return {
            'status': 'error',
            'user_email': user_email,
            'message': str(e),
            'processed_count': processed_count if 'processed_count' in locals() else 0
        }

@celery.task
def analyze_email_content_task(email_id):
    """
    Background task to analyze a single email's content
    
    Args:
        email_id (str): Email ID to analyze
        
    Returns:
        dict: Analysis results
    """
    try:
        email = Email.query.get(email_id)
        if not email:
            return {'status': 'error', 'message': 'Email not found'}
        
        # Skip if already analyzed
        if email.summary and email.category:
            return {'status': 'success', 'message': 'Email already analyzed'}
        
        # Prepare email data for analysis
        email_data = {
            'sender': email.sender,
            'subject': email.subject,
            'body_text': email.body_text,
            'has_attachments': email.has_attachments
        }
        
        # Analyze with LLM
        llm_service = LLMService()
        analysis = llm_service.analyze_email(email_data)
        
        # Update email with analysis
        email.sentiment = analysis.get('sentiment')
        email.priority = analysis.get('priority')
        email.category = analysis.get('category')
        email.summary = analysis.get('summary')
        email.action_required = analysis.get('action_required')
        
        db.session.commit()
        
        logger.info(f"Successfully analyzed email {email_id}")
        return {
            'status': 'success',
            'email_id': email_id,
            'analysis': analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing email {email_id}: {str(e)}")
        db.session.rollback()
        return {
            'status': 'error',
            'email_id': email_id,
            'message': str(e)
        }

@celery.task
def cleanup_old_emails_task(days_old=30):
    """
    Background task to cleanup old processed emails
    
    Args:
        days_old (int): Delete emails older than this many days
        
    Returns:
        dict: Cleanup results
    """
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Count emails to be deleted
        old_emails = Email.query.filter(Email.date_processed < cutoff_date)
        count_to_delete = old_emails.count()
        
        # Delete old emails
        old_emails.delete()
        db.session.commit()
        
        logger.info(f"Cleanup task completed: {count_to_delete} emails deleted")
        return {
            'status': 'success',
            'deleted_count': count_to_delete,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        db.session.rollback()
        return {
            'status': 'error',
            'message': str(e)
        }

if __name__ == '__main__':
    celery.start()