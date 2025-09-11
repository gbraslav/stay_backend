import re
from email_validator import validate_email as email_validate, EmailNotValidError

def validate_email(email):
    """
    Validate email address format
    
    Args:
        email (str): Email address to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Normalize the email address
        valid = email_validate(email)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)

def validate_oauth_token(token_data):
    """
    Validate OAuth token data structure
    
    Args:
        token_data (dict): OAuth token data
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(token_data, dict):
        return False, "Token data must be a dictionary"
    
    required_fields = ['access_token']
    missing_fields = [field for field in required_fields if not token_data.get(field)]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate token format (basic check)
    access_token = token_data.get('access_token', '')
    if len(access_token) < 20:
        return False, "Invalid access token format"
    
    return True, None

def validate_pagination_params(limit, offset):
    """
    Validate pagination parameters
    
    Args:
        limit (int): Maximum number of items to return
        offset (int): Number of items to skip
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        limit = int(limit) if limit is not None else 50
        offset = int(offset) if offset is not None else 0
        
        if limit < 1 or limit > 100:
            return False, "Limit must be between 1 and 100"
            
        if offset < 0:
            return False, "Offset must be non-negative"
            
        return True, None
        
    except (ValueError, TypeError):
        return False, "Limit and offset must be valid integers"