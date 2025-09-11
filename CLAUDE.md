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

**If using Python (FastAPI/Django):**
- `pip install -r requirements.txt` - Install dependencies
- `python -m uvicorn main:app --reload` - Start FastAPI development server
- `python manage.py runserver` - Start Django development server (if Django)
- `pytest` - Run tests
- `python -m flake8` or `ruff check` - Run linting

