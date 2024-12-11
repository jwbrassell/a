# Contributing Guidelines

## Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure your environment variables
5. Initialize the database:
   ```bash
   flask db upgrade
   python init_db.py
   ```

## Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose
- Write unit tests for new features

## Plugin Development

1. Create a new directory in `app/plugins/`
2. Include `__init__.py` with plugin registration
3. Follow the plugin architecture pattern:
   - routes.py for endpoints
   - models.py for database models
   - templates/ for HTML templates

## Git Workflow

1. Create a feature branch from main
2. Make your changes
3. Write/update tests
4. Submit a pull request
5. Ensure CI passes
6. Request code review

## Database Changes

1. Create migrations using:
   ```bash
   flask db migrate -m "Description of changes"
   ```
2. Review migration file
3. Apply migrations:
   ```bash
   flask db upgrade
   ```

## Testing

- Write unit tests for new features
- Run tests before submitting PR:
  ```bash
  python -m pytest
  ```
- Maintain test coverage above 80%

## Documentation

- Update relevant documentation when making changes
- Document new features in markdown files
- Include docstrings in code
- Keep API documentation current
