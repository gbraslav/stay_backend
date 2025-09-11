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

- **API Base URL**: http://localhost:5000/api/
- **Documentation**: http://localhost:5000/docs/
- **Health Check**: http://localhost:5000/api/health

## API Endpoints

### Authentication
- `POST /api/add_user` - Add user with OAuth2 token

### Email Processing
- `POST /api/process_emails` - Process user's emails
- `GET /api/emails` - List processed emails with filtering
- `GET /api/emails/{email_id}` - Get specific email details
- `GET /api/emails/summary` - Get email statistics

### Health
- `GET /api/health` - Service health check

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
uv run gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Or activate environment first
source .venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 run:app
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
EXPOSE 5000

# Run the application
CMD ["uv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
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