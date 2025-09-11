from flask import request, jsonify, current_app
from app.api import api_bp
from app.models import Email
from app.utils import GoogleAuthService, validate_oauth_token
from app.utils.token_storage import token_storage
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
        
        # Store token in memory for later use
        token_storage.store_token(user_email, token_data)
        logger.info(f"Stored token for user: {user_email}")
        
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
    """Process emails for a user with LLM analysis
    ---
    tags:
      - Emails
    parameters:
      - in: body
        name: request_data
        description: OAuth token and processing parameters
        required: true
        schema:
          type: object
          properties:
            oauth_token:
              $ref: '#/definitions/OAuthToken'
            days_back:
              type: integer
              default: 7
              example: 7
              description: Number of days to look back
            max_emails:
              type: integer
              default: 50
              example: 50
              description: Maximum number of emails to process
          required:
            - oauth_token
    responses:
      200:
        description: Emails processed successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: "Processed 25 emails"
            processed_count:
              type: integer
              example: 25
            total_fetched:
              type: integer
              example: 30
            errors_count:
              type: integer
              example: 0
            processed_emails:
              type: array
              items:
                $ref: '#/definitions/EmailSummary'
      400:
        description: Invalid request or missing OAuth token
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error
        schema:
          $ref: '#/definitions/ErrorResponse'
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
    """Get live emails from Gmail API using stored tokens
    ---
    tags:
      - Emails
    parameters:
      - in: query
        name: user_email
        type: string
        required: true
        description: User's Gmail address
        example: "user@gmail.com"
      - in: query
        name: sender
        type: string
        required: false
        description: Filter by sender email
        example: "boss@company.com"
      - in: query
        name: subject
        type: string
        required: false
        description: Filter by subject keywords
        example: "meeting"
      - in: query
        name: limit
        type: integer
        required: false
        default: 50
        description: Number of emails to return
        example: 10
      - in: query
        name: days_back
        type: integer
        required: false
        default: 7
        description: Days to look back
        example: 3
    responses:
      200:
        description: Emails retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            emails:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    example: "1234567890abcdef"
                  sender:
                    type: string
                    example: "sender@example.com"
                  subject:
                    type: string
                    example: "Important Meeting"
                  date_received:
                    type: string
                    format: date-time
                    example: "2024-09-11T10:30:00Z"
                  snippet:
                    type: string
                    example: "Hi, let's schedule a meeting..."
                  has_attachments:
                    type: boolean
                    example: false
                  labels:
                    type: string
                    example: "INBOX,UNREAD"
            total_fetched:
              type: integer
              example: 25
            source:
              type: string
              example: "gmail_api_live"
            user_email:
              type: string
              example: "user@gmail.com"
            filters_applied:
              type: object
              properties:
                sender:
                  type: string
                  nullable: true
                subject:
                  type: string
                  nullable: true
                days_back:
                  type: integer
                limit:
                  type: integer
      400:
        description: Invalid parameters
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: No valid token found for user
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        # Get query parameters
        user_email = request.args.get('user_email')
        sender = request.args.get('sender')
        subject = request.args.get('subject')
        limit = request.args.get('limit', 50)
        days_back = request.args.get('days_back', 7)
        
        # Validate parameters
        if not user_email:
            return jsonify({
                'status': 'error',
                'message': 'user_email parameter required'
            }), 400
        
        try:
            limit = int(limit)
            days_back = int(days_back)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'limit and days_back must be valid integers'
            }), 400
        
        # Check if we have stored tokens for this user
        if not token_storage.is_token_valid(user_email):
            return jsonify({
                'status': 'error',
                'message': 'No valid token found for user. Please call /add_user first.'
            }), 401
        
        # Get stored token data
        token_data = token_storage.get_token(user_email)
        
        # Create credentials and Gmail service
        auth_service = GoogleAuthService()
        credentials = auth_service.create_credentials_from_token({
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'scope': token_data.get('scope')
        })
        
        gmail_service = GmailService(credentials)
        email_parser = EmailParser()
        
        # Build Gmail query string
        query_parts = []
        if sender:
            query_parts.append(f'from:{sender}')
        if subject:
            query_parts.append(f'subject:"{subject}"')
        
        query_string = ' '.join(query_parts) if query_parts else None
        
        # Fetch messages from Gmail API
        messages = gmail_service.get_recent_messages(
            days=days_back, 
            max_results=limit,
            query=query_string
        )
        
        # Parse messages
        emails_data = []
        for message in messages:
            try:
                parsed_email = email_parser.parse_gmail_message(message, user_email)
                if parsed_email:
                    # Convert to summary format
                    summary = {
                        'id': parsed_email['id'],
                        'sender': parsed_email['sender'],
                        'subject': parsed_email['subject'],
                        'date_received': parsed_email.get('date_received'),
                        'snippet': parsed_email.get('snippet', '')[:200],  # First 200 chars
                        'has_attachments': parsed_email.get('has_attachments', False),
                        'labels': parsed_email.get('labels', '')
                    }
                    emails_data.append(summary)
            except Exception as e:
                logger.warning(f"Error parsing message {message.get('id', 'unknown')}: {e}")
                continue
        
        return jsonify({
            'status': 'success',
            'emails': emails_data,
            'total_fetched': len(emails_data),
            'source': 'gmail_api_live',
            'user_email': user_email,
            'filters_applied': {
                'sender': sender,
                'subject': subject,
                'days_back': days_back,
                'limit': limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_emails for user {user_email}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {repr(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_type': type(e).__name__
        }), 500

@api_bp.route('/emails/<email_id>', methods=['GET'])
def get_email_details(email_id):
    """Get full details of a specific email from Gmail API
    ---
    tags:
      - Emails
    parameters:
      - in: path
        name: email_id
        type: string
        required: true
        description: Gmail message ID
        example: "1234567890abcdef"
      - in: query
        name: user_email
        type: string
        required: true
        description: User's Gmail address
        example: "user@gmail.com"
    responses:
      200:
        description: Email details retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            email:
              $ref: '#/definitions/EmailDetail'
            source:
              type: string
              example: "gmail_api_live"
      400:
        description: Missing required parameters
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: No valid token found for user
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Email not found in Gmail or access denied
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        # Get user email from query parameter
        user_email = request.args.get('user_email')
        
        if not user_email:
            return jsonify({
                'status': 'error',
                'message': 'user_email parameter required'
            }), 400
        
        # Check if we have stored tokens for this user
        if not token_storage.is_token_valid(user_email):
            return jsonify({
                'status': 'error',
                'message': 'No valid token found for user. Please call /add_user first.'
            }), 401
        
        # Get stored token data
        token_data = token_storage.get_token(user_email)
        
        # Create credentials and Gmail service
        auth_service = GoogleAuthService()
        credentials = auth_service.create_credentials_from_token({
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'scope': token_data.get('scope')
        })
        
        gmail_service = GmailService(credentials)
        email_parser = EmailParser()
        
        # Fetch email details from Gmail
        try:
            message = gmail_service.get_message_details(email_id)
        except Exception as gmail_error:
            logger.warning(f"Gmail API error for message {email_id}: {gmail_error}")
            return jsonify({
                'status': 'error',
                'message': 'Email not found in Gmail or access denied'
            }), 404
        
        # Parse the message
        parsed_email = email_parser.parse_gmail_message(message, user_email)
        
        if not parsed_email:
            return jsonify({
                'status': 'error',
                'message': 'Failed to parse email content'
            }), 500
        
        # Return full email details
        return jsonify({
            'status': 'success',
            'email': parsed_email,
            'source': 'gmail_api_live'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_email_details for email {email_id}, user {user_email}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_type': type(e).__name__
        }), 500

@api_bp.route('/emails/summary', methods=['GET'])
def get_emails_summary():
    """Get summary statistics for user's processed emails
    ---
    tags:
      - Emails
    parameters:
      - in: query
        name: user_email
        type: string
        required: true
        description: User's Gmail address
        example: "user@gmail.com"
    responses:
      200:
        description: Email summary retrieved successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            summary:
              type: object
              properties:
                total_emails:
                  type: integer
                  example: 150
                  description: Total number of processed emails
                high_priority:
                  type: integer
                  example: 12
                  description: Number of high priority emails
                action_required:
                  type: integer
                  example: 8
                  description: Number of emails requiring action
                categories:
                  type: object
                  description: Email count by category
                  additionalProperties:
                    type: integer
                  example:
                    work: 80
                    personal: 35
                    promotional: 25
                    social: 10
      400:
        description: Missing user_email parameter
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error
        schema:
          $ref: '#/definitions/ErrorResponse'
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