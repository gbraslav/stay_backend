# CLAUDE.md

# Project Overview: Email Processing API

This is the back-end service for the StayOnTop project. The client will be a mobile app.
This project implements a Python RESTful API for reading emails from gmail and analyzing the content using a LLM. It provides endpoints for receiving the gmail oauth2 credentials and then connecting, parsing, and managing email data, including attachments and sender/recipient information.


## Key Components

- **Flask Application**: The core web framework for handling API requests.
- **Email Parser Module**: Responsible for extracting relevant data from raw email content.
- **Email Service/Worker**: Handles asynchronous tasks like sending notifications or further processing. (e.g., Celery)

## API Endpoints

- **POST /add_user**: Receives user oauth2 token from the client.
    - **Input**: oauth2 token for the users gmail.
    - **Output**: JSON object with a status of the gmail connection (success/fail).
- **GET /emails/{email_id}**: Retrieves details of a specific processed email.
    - **Output**: JSON object with full email details.
- **GET /emails**: Retrieves a list of processed emails with optional filtering/pagination.
    - **Query Parameters**: `sender`, `subject`, `limit`, `offset`.
    - **Output**: JSON array of email summaries.

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
- Health check: http://localhost:5000/api/health
- API documentation: http://localhost:5000/docs/
- Main API endpoints: http://localhost:5000/api/

### Development Workflow
- Use `make` commands for common tasks (see `make help`)
- Code formatting: `make format`
- Run tests: `make test`
- Run all checks: `make check`

