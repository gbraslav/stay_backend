# StayOnTop Email Processing API

A Python Flask-based RESTful API for processing Gmail emails using OAuth2 authentication and LLM-powered analysis.

## Features

- **Gmail Integration**: Connect to Gmail using OAuth2 authentication
- **Email Processing**: Parse and extract key information from emails
- **LLM Analysis**: Analyze email content for sentiment, priority, and categorization
- **Background Processing**: Asynchronous email processing with Celery
- **RESTful API**: Clean API endpoints for mobile app integration
- **Comprehensive Testing**: Full test suite with pytest
- **API Documentation**: Interactive Swagger/OpenAPI documentation

## Tech Stack

- **Framework**: Flask 3.0.3
- **Database**: SQLAlchemy with SQLite (dev) / PostgreSQL (prod)
- **Authentication**: Google OAuth2
- **LLM Integration**: OpenAI GPT-3.5-turbo
- **Background Tasks**: Celery with Redis
- **Testing**: pytest
- **Documentation**: Swagger/OpenAPI with Flasgger

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd stay_backend

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (creates virtual environment automatically)
uv sync
```

### 2. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- Google OAuth2 credentials from Google Cloud Console
- OpenAI API key
- Redis connection string (if using external Redis)

### 3. Run the Application

```bash
# Development server (uv automatically activates the virtual environment)
uv run python run.py

# Or with Flask CLI
uv run flask --app run.py --debug run

# Alternative: activate the environment and run normally
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python run.py
```

### 4. Start Background Worker (Optional)

```bash
# In a separate terminal (uv automatically uses the virtual environment)
uv run celery -A celery_worker.celery worker --loglevel=info
```

### 5. Access the API

- **API Base URL**: http://localhost:5001/api/
- **Documentation**: http://localhost:5001/docs/
- **Health Check**: http://localhost:5001/api/health

## API Endpoints

### Health Check

#### `GET /api/health`
Check service health and status.

**Response:**
```json
{
  "status": "healthy",
  "service": "stay_backend", 
  "version": "1.0.0"
}
```

**Example:**
```bash
curl http://localhost:5001/api/health
```

---

### Authentication

#### `POST /api/add_user`
Store user's OAuth2 token for Gmail access. This must be called first before using other endpoints.

**Request Body:**
```json
{
  "access_token": "ya29.a0AfH6SMC...",
  "refresh_token": "1//04...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "https://www.googleapis.com/auth/gmail.readonly"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Gmail connection established successfully",
  "user_email": "user@gmail.com",
  "gmail_info": {
    "total_messages": 1500,
    "total_threads": 750
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Invalid token: access_token is required"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "ya29.a0AfH6SMC...",
    "refresh_token": "1//04...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "https://www.googleapis.com/auth/gmail.readonly"
  }'
```

---

### Email Retrieval (Live Gmail API)

#### `GET /api/emails`
Get live emails directly from Gmail API using stored tokens.

**Query Parameters:**
- `user_email` (required) - User's Gmail address
- `sender` (optional) - Filter by sender email
- `subject` (optional) - Filter by subject keywords
- `limit` (optional) - Number of emails to return (default: 50)
- `days_back` (optional) - Days to look back (default: 7)

**Response:**
```json
{
  "status": "success",
  "emails": [
    {
      "id": "1234567890abcdef",
      "sender": "sender@example.com",
      "subject": "Important Meeting",
      "date_received": "2024-09-11T10:30:00Z",
      "snippet": "Hi, let's schedule a meeting...",
      "has_attachments": false,
      "labels": "INBOX,UNREAD"
    }
  ],
  "total_fetched": 25,
  "source": "gmail_api_live",
  "user_email": "user@gmail.com",
  "filters_applied": {
    "sender": null,
    "subject": null,
    "days_back": 7,
    "limit": 50
  }
}
```

**Examples:**
```bash
# Get recent emails
curl "http://localhost:5001/api/emails?user_email=user@gmail.com"

# Filter by sender
curl "http://localhost:5001/api/emails?user_email=user@gmail.com&sender=boss@company.com"

# Filter by subject and limit results
curl "http://localhost:5001/api/emails?user_email=user@gmail.com&subject=meeting&limit=10"
```

#### `GET /api/emails/{email_id}`
Get full details of a specific email from Gmail API.

**Path Parameters:**
- `email_id` - Gmail message ID (from `/emails` response)

**Query Parameters:**
- `user_email` (required) - User's Gmail address

**Response:**
```json
{
  "status": "success",
  "email": {
    "id": "1234567890abcdef",
    "user_id": "user@gmail.com",
    "sender": "sender@example.com",
    "recipient": "user@gmail.com",
    "subject": "Important Meeting",
    "body_text": "Hi, let's schedule a meeting for next week...",
    "body_html": "<p>Hi, let's schedule a meeting for next week...</p>",
    "date_received": "2024-09-11T10:30:00Z",
    "thread_id": "thread123",
    "labels": "INBOX,UNREAD",
    "has_attachments": true,
    "attachment_count": 2,
    "snippet": "Hi, let's schedule a meeting..."
  },
  "source": "gmail_api_live"
}
```

**Example:**
```bash
curl "http://localhost:5001/api/emails/1234567890abcdef?user_email=user@gmail.com"
```

---

### Email Processing & Analysis

#### `POST /api/process_emails`
Fetch emails from Gmail, analyze with LLM, and store in database.

**Request Body:**
```json
{
  "oauth_token": {
    "access_token": "ya29.a0AfH6SMC...",
    "refresh_token": "1//04..."
  },
  "days_back": 7,
  "max_emails": 50
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Processed 25 emails",
  "processed_count": 25,
  "total_fetched": 30,
  "errors_count": 0,
  "processed_emails": [
    {
      "id": "1234567890abcdef",
      "sender": "boss@company.com",
      "subject": "Project Update",
      "priority": "high",
      "category": "work",
      "sentiment": "neutral",
      "action_required": true,
      "summary": "Boss requesting project status update by Friday"
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/process_emails \
  -H "Content-Type: application/json" \
  -d '{
    "oauth_token": {
      "access_token": "ya29.a0AfH6SMC...",
      "refresh_token": "1//04..."
    },
    "days_back": 7,
    "max_emails": 50
  }'
```

#### `GET /api/emails/summary`
Get statistics about processed emails stored in database.

**Query Parameters:**
- `user_email` (required) - User's Gmail address

**Response:**
```json
{
  "status": "success",
  "summary": {
    "total_emails": 150,
    "high_priority": 12,
    "action_required": 8,
    "categories": {
      "work": 80,
      "personal": 35,
      "promotional": 25,
      "social": 10
    }
  }
}
```

**Example:**
```bash
curl "http://localhost:5001/api/emails/summary?user_email=user@gmail.com"
```

---

### Error Responses

All endpoints return consistent error responses:

```json
{
  "status": "error",
  "message": "Descriptive error message",
  "error_type": "ValueError"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing/invalid parameters)
- `401` - Unauthorized (no valid token found)
- `404` - Not Found (email/resource doesn't exist)  
- `500` - Internal Server Error

---

### Authentication Flow

1. **Get OAuth2 token** from Google OAuth2 flow in your client app
2. **Store token** via `POST /api/add_user` 
3. **Use stored token** for subsequent API calls

**Important Notes:**
- Tokens are stored in memory and cleared on server restart
- All email endpoints require prior token storage via `/add_user`
- `/emails` and `/emails/{id}` fetch live data from Gmail API
- `/process_emails` analyzes and stores emails in database for later querying

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage (already configured in pyproject.toml)
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_api.py

# Run with verbose output
uv run pytest -v

# Install development dependencies if not already installed
uv sync --group dev
```

## Development Commands

```bash
# Install all dependencies (including dev dependencies)
uv sync

# Install only production dependencies
uv sync --no-group dev

# Add a new dependency
uv add flask-limiter

# Add a development dependency
uv add --group dev black

# Run tests
uv run pytest

# Run code formatting
uv run black app/ tests/

# Run linting
uv run ruff check app/ tests/

# Run type checking
uv run mypy app/

# Start development server
uv run python run.py

# Start Celery worker
uv run celery -A celery_worker.celery worker --loglevel=info

# Generate requirements.txt (for compatibility)
uv export --no-hashes --format requirements-txt > requirements.txt
```

## Project Structure

```
stay_backend/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration settings
│   ├── docs.py              # OpenAPI documentation
│   ├── models/              # Database models
│   │   ├── __init__.py
│   │   └── email.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── gmail_service.py
│   │   ├── email_parser.py
│   │   └── llm_service.py
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   └── endpoints.py
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── auth.py
│       └── validators.py
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── run.py                  # Application entry point
├── celery_worker.py        # Background tasks
├── .env.example            # Environment template
└── README.md
```

## Configuration

The application uses environment-based configuration:

- **Development**: Uses SQLite database, debug mode enabled
- **Production**: Configure with PostgreSQL, disable debug mode

Key environment variables:
- `FLASK_ENV`: development/production
- `DATABASE_URL`: Database connection string
- `GOOGLE_CLIENT_ID/SECRET`: OAuth2 credentials
- `OPENAI_API_KEY`: OpenAI API access
- `CELERY_BROKER_URL`: Redis broker URL

## Deployment

### Using Gunicorn

```bash
# With uv
uv run gunicorn -w 4 -b 0.0.0.0:5001 run:app

# Or activate environment first
source .venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5001 run:app
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Expose port
EXPOSE 5001

# Run the application
CMD ["uv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "run:app"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

Curl examples:
curl -X POST localhost:5001/api/add_user -H "Content-Type: application/json" -d '{"access_token":"ya29.a0AS3H6NwxGnjc7N2xRLJWy1_CR0VjEw34yEl4dJ4H3tZMgBAuKVjyajJVPT0rlWogNYM4IJaDALJBAODdxGonh9bHFIRvohVockyGKf64E2q8LqobW64WXmM3DI6iqmb4UUWDdqoecQE-Kwq2TmKLVYAnxMw80Pjyfk3JyTc92I1m1nXzVxeIaCsgZ_ojZN1_3jxYZ7kaCgYKAZoSARYSFQHGX2MiIKgRzlhoc_ZsF4byITtUtw0206"}'

curl "localhost:5001/api/emails?user_email=gbraslavsky@gmail.com"

curl "localhost:5001/api/emails/199399dfc60e38c8?user_email=gbraslavsky@gmail.com"

