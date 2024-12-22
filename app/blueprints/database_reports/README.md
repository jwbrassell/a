# Database Reports Blueprint

This Flask blueprint provides functionality for managing database connections and creating SQL-based reports.

## Structure

- `__init__.py` - Blueprint initialization and module imports
- `routes.py` - Central route registration
- `models.py` - Database models for connections and reports
- `connections.py` - Database connection management
- `queries.py` - SQL query testing and execution
- `reports.py` - Report management
- `utils.py` - Helper functions

## Features

- Database Connection Management
  - Support for MySQL, Oracle, and SQLite
  - Secure credential storage using Vault
  - Connection testing

- Report Management
  - Direct SQL query input
  - Column formatting options
  - Public/private reports
  - Tag-based organization

- Security
  - CSRF protection
  - Permission-based access control
  - SQL query validation (SELECT only)

## Usage

### Creating a Database Connection

1. Navigate to /database_reports/connections
2. Click "New Connection"
3. Fill in connection details:
   - Name
   - Description
   - Database Type (MySQL, Oracle, SQLite)
   - Connection Parameters
   - Credentials

### Creating a Report

1. Navigate to /database_reports/reports/new
2. Select a database connection
3. Enter your SQL query
4. Configure column display settings
5. Set report visibility (public/private)
6. Add tags for organization

### Testing Queries

- Use the "Test Query" button when creating/editing reports
- Only SELECT statements are allowed
- Column types are automatically detected
- Preview data is available before saving

### Viewing Reports

- Access your reports from the dashboard
- Public reports are visible to all users
- Private reports are only visible to their creators
- Use tags and search to find specific reports

## Security Notes

1. Database credentials are stored securely in Vault
2. Only SELECT queries are allowed
3. Connections and reports are protected by permissions
4. CSRF protection is enabled for all forms
5. SQL injection protection through parameterized queries

## Development

To add new features:

1. Add models to `models.py`
2. Create route handlers in appropriate module
3. Update templates in `templates/`
4. Register routes in module's route file
5. Import routes in `routes.py`

## Dependencies

- Flask
- SQLAlchemy
- Flask-Login
- oracledb
- mysql-connector
- sqlite3
- vault_utility
