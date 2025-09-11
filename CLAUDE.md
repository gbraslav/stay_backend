# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This is a new backend project for "Stay" application. The repository is currently empty and ready for initialization.

## Expected Project Structure

Based on the directory name `stay_backend`, this appears to be intended as a backend service. When initialized, consider the following structure and commands:

### Common Backend Frameworks and Commands

**If using Node.js/Express:**
- `npm install` - Install dependencies
- `npm start` - Start the server
- `npm run dev` - Start development server with hot reload
- `npm test` - Run test suite
- `npm run lint` - Run linting
- `npm run build` - Build for production

**If using Python (FastAPI/Django):**
- `pip install -r requirements.txt` - Install dependencies
- `python -m uvicorn main:app --reload` - Start FastAPI development server
- `python manage.py runserver` - Start Django development server (if Django)
- `pytest` - Run tests
- `python -m flake8` or `ruff check` - Run linting

**If using Go:**
- `go mod tidy` - Install/update dependencies
- `go run main.go` - Run the application
- `go test ./...` - Run all tests
- `go build` - Build binary

## Development Setup

When the project is initialized, this section should include:
- Environment setup instructions
- Database setup (if applicable)
- Required environment variables
- Docker setup (if containerized)

## Architecture Notes

This section should be updated once the project structure is established to include:
- API endpoint organization
- Database schema approach
- Authentication/authorization patterns
- Key architectural decisions