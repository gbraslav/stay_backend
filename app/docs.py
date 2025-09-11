"""
OpenAPI/Swagger documentation definitions
"""

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "StayOnTop Email Processing API",
        "description": "RESTful API for processing Gmail emails using OAuth2 and LLM analysis",
        "version": "1.0.0",
        "contact": {
            "name": "StayOnTop API Support",
            "email": "support@stayontop.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/api",
    "schemes": [
        "http",
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json"
    ],
    "securityDefinitions": {
        "OAuth2": {
            "type": "oauth2",
            "flow": "implicit",
            "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
            "scopes": {
                "https://www.googleapis.com/auth/gmail.readonly": "Read Gmail messages"
            }
        }
    },
    "tags": [
        {
            "name": "Authentication",
            "description": "OAuth2 authentication and user management"
        },
        {
            "name": "Emails",
            "description": "Email processing and retrieval"
        },
        {
            "name": "Health",
            "description": "API health and status"
        }
    ]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

# API Response schemas
error_response_schema = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["error"],
            "example": "error"
        },
        "message": {
            "type": "string",
            "example": "Error description"
        }
    },
    "required": ["status", "message"]
}

success_response_schema = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success"],
            "example": "success"
        },
        "message": {
            "type": "string",
            "example": "Operation completed successfully"
        }
    },
    "required": ["status", "message"]
}

email_summary_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "example": "message_id_123"},
        "sender": {"type": "string", "example": "sender@example.com"},
        "subject": {"type": "string", "example": "Important Meeting"},
        "date_received": {"type": "string", "format": "date-time"},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "category": {"type": "string", "enum": ["work", "personal", "promotional", "notification", "other"]},
        "summary": {"type": "string", "example": "Brief email summary"},
        "action_required": {"type": "boolean"},
        "has_attachments": {"type": "boolean"}
    }
}

email_detail_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "user_id": {"type": "string"},
        "sender": {"type": "string"},
        "recipient": {"type": "string"},
        "subject": {"type": "string"},
        "body_text": {"type": "string"},
        "body_html": {"type": "string"},
        "date_received": {"type": "string", "format": "date-time"},
        "date_processed": {"type": "string", "format": "date-time"},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "category": {"type": "string"},
        "summary": {"type": "string"},
        "action_required": {"type": "boolean"},
        "thread_id": {"type": "string"},
        "has_attachments": {"type": "boolean"},
        "attachment_count": {"type": "integer"},
        "labels": {"type": "string"}
    }
}

oauth_token_schema = {
    "type": "object",
    "properties": {
        "access_token": {
            "type": "string",
            "description": "OAuth2 access token",
            "example": "ya29.a0AfH6SMC..."
        },
        "refresh_token": {
            "type": "string",
            "description": "OAuth2 refresh token (optional)",
            "example": "1//04..."
        },
        "token_type": {
            "type": "string",
            "example": "Bearer"
        },
        "expires_in": {
            "type": "integer",
            "example": 3600
        },
        "scope": {
            "type": "string",
            "example": "https://www.googleapis.com/auth/gmail.readonly"
        }
    },
    "required": ["access_token"]
}