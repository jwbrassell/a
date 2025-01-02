# Application Setup Documentation

This directory contains documentation and scripts for setting up the Flask application in an environment where Vault, nginx, and gunicorn are pre-configured.

## Prerequisites

- Python 3.x
- Pre-configured HashiCorp Vault running on http://127.0.0.1:8200
- Pre-configured nginx for SSL/TLS termination and reverse proxy
- Pre-configured gunicorn for WSGI server
- PostgreSQL (recommended)

## Setup Process

1. Initial Setup:
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Configure environment
   cp .env.example .env
   ```

2. Initialize database:
   ```bash
   # Initialize database with default roles and permissions
   python init_database.py

   # Set up database migrations
   flask db init
   flask db migrate
   flask db upgrade
   ```

4. Configure system service:
   ```bash
   sudo cp flask_app.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl start flask_app
   ```

## Environment Files

### .env
Contains application configuration:
```
FLASK_APP=app.py
FLASK_ENV=production
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=<app-token>
```

## Security Notes

- All Vault communication is restricted to localhost
- nginx handles SSL/TLS termination
- Environment files should have 600 permissions (user read/write only)
- Application uses a limited-privilege Vault token with specific policies

## Production Considerations

- Works with pre-configured production WSGI server (gunicorn)
- Vault token renewal is handled automatically by the application
- The application uses a limited-privilege Vault token with specific policies
- nginx handles SSL/TLS termination and acts as a reverse proxy
- gunicorn manages multiple worker processes

## Troubleshooting

1. If the application fails to start:
   ```bash
   # Check service status
   sudo systemctl status flask_app

   # View application logs
   sudo journalctl -u flask_app

   # Check nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

2. If database migrations fail:
   ```bash
   # Remove existing migrations
   rm -rf migrations/

   # Reinitialize migrations
   flask db init
   flask db migrate
   flask db upgrade
   ```

3. Permission issues:
   ```bash
   # Check directory permissions
   ls -l /var/log/flask_app
   ls -l /var/run/flask_app
   ls -l instance/
   ```

## Directory Structure

```
.
├── app/                    # Application package
├── config/                 # Configuration files
├── instance/              # Instance-specific files
├── migrations/            # Database migrations
├── setup/                 # Setup documentation
└── flask_app.service      # Systemd service file
```

## Maintenance

- Monitor application logs in /var/log/flask_app/
- Keep Python dependencies updated
- Regularly check nginx and gunicorn configurations
- Monitor system resources (CPU, memory, disk usage)
- Backup database regularly
