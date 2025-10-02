# CLAUDE.md

# Project Overview: Email Processing API

This is the back-end service for the StayOnTop project. The client will be a mobile app.
This project implements a Python RESTful API for reading emails from gmail and analyzing the content using a LLM. It provides endpoints for receiving the gmail oauth2 credentials and then connecting, parsing, and managing email data, including attachments and sender/recipient information.


## Key Components

- **Flask Application**: The core web framework for handling API requests.
- **Email Parser Module**: Responsible for extracting relevant data from raw email content.
- **Email Service/Worker**: Handles asynchronous tasks like sending notifications or further processing. (e.g., Celery)

## API Endpoints

### Health & Status
- **GET /health**: Health check endpoint
    - **Output**: JSON object with service status, name, and version
    - **Response**: `{"status": "healthy", "service": "stay_backend", "version": "1.0.0"}`

### Authentication & User Management
- **POST /add_user**: Receives user oauth2 token from the client (memory-only storage)
    - **Input**: OAuth2 token object with `access_token`, `refresh_token`, `token_type`, `expires_in`, `scope`
    - **Output**: JSON object with Gmail connection status, user email, and Gmail info (total messages/threads)
    - **Storage**: Tokens stored in memory only, lost on server restart

- **POST /add_persistent_user**: Receives user refresh token and returns session token with persistent storage
    - **Input**: Google refresh token (`{"refresh_token": "1//04..."}`)
    - **Processing**: Uses refresh token to get fresh access token, validates Gmail connection
    - **Output**: JSON object with session token, user info, and expiry time
    - **Storage**: Refresh token persisted to `user_tokens.json` file for future use
    - **Session Token**: Returns JWT-based session token (1 hour expiry) for API access

- **GET /sessions/status**: Get current session status and statistics
    - **Output**: JSON object with total sessions count and list of active users
    - **Response**: `{"status": "success", "sessions": {"total_sessions": 2, "users": ["user1@gmail.com", "user2@gmail.com"]}}`

### Email Processing & Retrieval
- **GET /emails**: Get live emails from Gmail API using stored tokens
    - **Query Parameters**: 
        - `user_email` (required): User's Gmail address
        - `sender` (optional): Filter by sender email
        - `subject` (optional): Filter by subject keywords
        - `limit` (optional, default: 50): Number of emails to return
        - `days_back` (optional, default: 7): Days to look back
    - **Output**: JSON array of email summaries with metadata (id, sender, subject, date, snippet, attachments, labels)

- **GET /emails/{email_id}**: Get full details of a specific email from Gmail API
    - **Path Parameter**: `email_id` - Gmail message ID
    - **Query Parameters**: `user_email` (required) - User's Gmail address
    - **Output**: JSON object with complete email details including body, headers, attachments

- **GET /emails/summary**: Get summary statistics for user's processed emails
    - **Query Parameters**: `user_email` (required) - User's Gmail address
    - **Output**: JSON object with email statistics (total emails, high priority count, action required count, categories breakdown)

- **POST /process_single_email**: Process single email with ChatGPT
    - **Input**: `email_id` and `user_email`
    - **Output**: JSON object with ChatGPT response for the specific email

### Priority & Monitoring
- **GET /get_10_emails_concat**: Aggregates last 10 emails from all users with active access tokens
    - **Input**: None (uses all active users automatically)
    - **Processing**: Fetches recent emails from all users, parses content, concatenates with separators
    - **Output**: JSON with concatenated email string, user/email counts, and error statistics
    - **Separators**: Uses 80 asterisk characters (`*`) between each email for readability

## Code Style and Best Practices

- Adhere to PEP 8 for Python code styling.
- Use clear and descriptive variable/function names.
- Implement comprehensive unit and integration tests.
- Ensure proper error handling and logging.
- Document API endpoints using OpenAPI/Swagger specifications.

## Workflow

1.  **Receive oauth2 credentials for Gmail**: The `/emails` endpoint receives incoming email data.
2.  **Parse Email**: The email parser extracts key information (sender, recipient, subject, body, attachments).
3.  **Store Data**: to be implemented later. Parsed email data is stored in the database.
4.  **Asynchronous Processing (Optional)**: A background worker can be triggered for tasks like attachment scanning or notification sending.
5.  **Retrieve/Manage**: Other endpoints allow for querying and managing processed emails.

## Important Considerations

- **Security**: Implement proper authentication and authorization for API access. Sanitize all input to prevent injection attacks.
- **Scalability**: Design for potential growth in email volume. Consider message queues for handling high loads.
- **Error Handling**: Provide informative error responses for API consumers.
- **Testing**: Write tests for all critical components and API endpoints.



## Expected Project Structure

Based on the directory name `stay_backend`, this appears to be intended as a backend service. When initialized, consider the following structure and commands:

### Common Backend Frameworks and Commands

**Python Flask with uv:**
- `uv sync` - Install all dependencies (including dev dependencies)
- `uv sync --no-group dev` - Install production dependencies only
- `uv run python run.py` - Start Flask development server
- `uv run pytest` - Run tests  
- `uv run ruff check app/ tests/` - Run linting
- `uv run black app/ tests/` - Run code formatting
- `uv run mypy app/` - Run type checking
- `make help` - Show all available Makefile commands

## Quick Development Setup

### Prerequisites
- Python 3.9+ installed
- uv package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Redis server (for background processing): `brew install redis` (macOS)
- Google Cloud Console project with Gmail API enabled
- OpenAI API account

### Setup Steps
```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from Google Cloud Console
# - OPENAI_API_KEY from OpenAI platform
# - TOKEN_STORAGE_FILE (optional): Path for persistent token storage (defaults to user_tokens.json)
# - JWT_SECRET_KEY (optional): Secret key for session tokens (defaults to dev key)
# - Other configuration as needed

# 3. Start Redis (in separate terminal)
redis-server

# 4. Run the application
uv run python run.py

# 5. Start background worker (in separate terminal, optional)
uv run celery -A celery_worker.celery worker --loglevel=info

# 6. Run tests
uv run pytest
```

### API Access
- Health check: http://localhost:5001/api/health
- API documentation: http://localhost:5001/docs/
- Main API endpoints: http://localhost:5001/api/

### Development Workflow
- Use `make` commands for common tasks (see `make help`)
- Code formatting: `make format`
- Run tests: `make test`
- Run all checks: `make check`
- update the documentation and claude.md file for each api change

