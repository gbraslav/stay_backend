from flask import request, jsonify, current_app
from app.api import api_bp
from app.models import Email
from app.utils import GoogleAuthService, validate_oauth_token, validate_pagination_params
from app.services import GmailService, EmailParser, LLMService
from app import db
import logging
import json

logger = logging.getLogger(__name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint
    ---
    tags:
      - Health
    responses:
      200:
        description: Service is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            service:
              type: string
              example: stay_backend
            version:
              type: string
              example: 1.0.0
    """
    return jsonify({
        'status': 'healthy',
        'service': 'stay_backend',
        'version': '1.0.0'
    }), 200

@api_bp.route('/add_user', methods=['POST'])
def add_user():
    """Add user with OAuth2 token
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: oauth_token
        description: OAuth2 token from Gmail
        required: true
        schema:
          $ref: '#/definitions/OAuthToken'
    responses:
      200:
        description: Gmail connection established successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Gmail connection established successfully
            user_email:
              type: string
              example: user@gmail.com
            gmail_info:
              type: object
              properties:
                total_messages:
                  type: integer
                  example: 1500
                total_threads:
                  type: integer
                  example: 750
      400:
        description: Invalid request or token
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Failed to validate Gmail connection
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error
        schema:
          $ref: '#/definitions/ErrorResponse'
    definitions:
      OAuthToken:
        type: object
        properties:
          access_token:
            type: string
            description: OAuth2 access token
            example: ya29.a0AfH6SMC...
          refresh_token:
            type: string
            description: OAuth2 refresh token (optional)
            example: 1//04...
          token_type:
            type: string
            example: Bearer
          expires_in:
            type: integer
            example: 3600
          scope:
            type: string
            example: https://www.googleapis.com/auth/gmail.readonly
        required:
          - access_token
      ErrorResponse:
        type: object
        properties:
          status:
            type: string
            enum: [error]
            example: error
          message:
            type: string
            example: Error description
        required:
          - status
          - message
    """
    try:
        # Get token data from request
        token_data = request.get_json()
        
        if not token_data:
            return jsonify({
                'status': 'error',
                'message': 'No token data provided'
            }), 400
        
        # Validate token structure
        is_valid, error_msg = validate_oauth_token(token_data)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': f'Invalid token: {error_msg}'
            }), 400
        
        # Create Google Auth service and credentials
        auth_service = GoogleAuthService()
        try:
            credentials = auth_service.create_credentials_from_token(token_data)
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': f'Invalid credentials: {str(e)}'
            }), 400
        
        # Validate credentials by testing connection
        is_valid, user_info = auth_service.validate_credentials(credentials)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': 'Failed to validate Gmail connection'
            }), 401
        
        # Get user email
        user_email = user_info.get('email')
        if not user_email:
            return jsonify({
                'status': 'error',
                'message': 'Unable to retrieve user email'
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Gmail connection established successfully',
            'user_email': user_email,
            'gmail_info': {
                'total_messages': user_info.get('messages_total', 0),
                'total_threads': user_info.get('threads_total', 0)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in add_user: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@api_bp.route('/process_emails', methods=['POST'])
def process_emails():
    """
    Process emails for a user
    POST /api/process_emails
    """
    try:
        # Get request data
        request_data = request.get_json()
        
        if not request_data or not request_data.get('oauth_token'):
            return jsonify({
                'status': 'error',
                'message': 'OAuth token required'
            }), 400
        
        # Get optional parameters
        days_back = request_data.get('days_back', 7)
        max_emails = request_data.get('max_emails', 50)
        
        # Create services
        auth_service = GoogleAuthService()
        credentials = auth_service.create_credentials_from_token(request_data['oauth_token'])
        user_email = auth_service.get_user_email(credentials)
        
        if not user_email:
            return jsonify({
                'status': 'error',
                'message': 'Unable to get user email'
            }), 400
        
        gmail_service = GmailService(credentials)
        email_parser = EmailParser()
        llm_service = LLMService()
        
        # Fetch recent messages
        messages = gmail_service.get_recent_messages(days=days_back, max_results=max_emails)
        
        processed_emails = []
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
                    continue
                
                # Analyze with LLM
                analysis = llm_service.analyze_email(parsed_email)
                
                # Combine parsed data with analysis
                email_data = {**parsed_email, **analysis}
                
                # Create Email object
                email_obj = Email(**email_data)
                db.session.add(email_obj)
                
                processed_emails.append(email_obj.to_summary_dict())
                
            except Exception as e:
                logger.warning(f"Error processing message {message.get('id', 'unknown')}: {e}")
                errors.append(f"Message {message.get('id', 'unknown')}: {str(e)}")
        
        # Commit to database
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database commit error: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to save processed emails'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(processed_emails)} emails',
            'processed_count': len(processed_emails),
            'total_fetched': len(messages),
            'errors_count': len(errors),
            'processed_emails': processed_emails[:10]  # Return first 10 for preview
        }), 200
        
    except Exception as e:
        logger.error(f"Error in process_emails: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@api_bp.route('/emails', methods=['GET'])
def get_emails():
    """
    Get list of emails with filtering and pagination
    GET /api/emails
    """
    try:
        # Get query parameters
        user_email = request.args.get('user_email')
        sender = request.args.get('sender')
        subject = request.args.get('subject')
        category = request.args.get('category')
        priority = request.args.get('priority')
        action_required = request.args.get('action_required')
        limit = request.args.get('limit', 50)
        offset = request.args.get('offset', 0)
        
        # Validate pagination
        is_valid, error_msg = validate_pagination_params(limit, offset)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
        
        limit = int(limit)
        offset = int(offset)
        
        if not user_email:
            return jsonify({
                'status': 'error',
                'message': 'user_email parameter required'
            }), 400
        
        # Build query
        query = Email.query.filter_by(user_id=user_email)
        
        # Apply filters
        if sender:
            query = query.filter(Email.sender.ilike(f'%{sender}%'))
        if subject:
            query = query.filter(Email.subject.ilike(f'%{subject}%'))
        if category:
            query = query.filter_by(category=category)
        if priority:
            query = query.filter_by(priority=priority)
        if action_required is not None:
            action_bool = action_required.lower() == 'true'
            query = query.filter_by(action_required=action_bool)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        emails = query.order_by(Email.date_received.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict
        emails_data = [email.to_summary_dict() for email in emails]
        
        return jsonify({
            'status': 'success',
            'emails': emails_data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': offset + limit < total_count,
                'has_prev': offset > 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_emails: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@api_bp.route('/emails/<email_id>', methods=['GET'])
def get_email_details(email_id):
    """
    Get details of a specific email
    GET /api/emails/{email_id}
    """
    try:
        email = Email.query.get(email_id)
        
        if not email:
            return jsonify({
                'status': 'error',
                'message': 'Email not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'email': email.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_email_details: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@api_bp.route('/emails/summary', methods=['GET'])
def get_emails_summary():
    """
    Get summary statistics for user's emails
    GET /api/emails/summary
    """
    try:
        user_email = request.args.get('user_email')
        
        if not user_email:
            return jsonify({
                'status': 'error',
                'message': 'user_email parameter required'
            }), 400
        
        # Get statistics
        total_emails = Email.query.filter_by(user_id=user_email).count()
        high_priority = Email.query.filter_by(user_id=user_email, priority='high').count()
        action_required = Email.query.filter_by(user_id=user_email, action_required=True).count()
        
        # Get category distribution
        categories = db.session.query(
            Email.category, 
            db.func.count(Email.category)
        ).filter_by(user_id=user_email).group_by(Email.category).all()
        
        category_stats = {category: count for category, count in categories}
        
        return jsonify({
            'status': 'success',
            'summary': {
                'total_emails': total_emails,
                'high_priority': high_priority,
                'action_required': action_required,
                'categories': category_stats
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_emails_summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500