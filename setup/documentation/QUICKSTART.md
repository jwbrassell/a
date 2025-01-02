# Quick Start Guide

## Prerequisites

Ensure you have the following pre-configured services running:
- Vault server running on http://127.0.0.1:8200
- nginx
- gunicorn
- PostgreSQL (recommended)

## First Time Setup

1. Clone and setup Python environment:
```bash
git clone [repository-url]
cd [repository-name]

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. Set up environment and database:
```bash
# Copy and configure environment variables
cp .env.example .env

# Initialize database and migrations
python init_database.py
flask db init
flask db migrate
flask db upgrade
```

## Running the App

### Development Mode
```bash
python app.py
```

### Production Mode
```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

### System Service
```bash
# Install and start the Flask app service
sudo cp flask_app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start flask_app
```

## File Locations

- App configuration: .env
- Database: instance/app.db (if using SQLite)
- Logs: /var/log/flask_app/ (when running as service)

## Notes

- Ensure Vault is running and accessible at http://127.0.0.1:8200 before starting the app
- The app integrates with the pre-configured Vault instance for secrets management
- nginx handles SSL/TLS termination in production
- gunicorn manages multiple worker processes for production deployment

## Troubleshooting

1. Check the application logs:
```bash
# If running as service
sudo journalctl -u flask_app

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

2. Verify permissions:
```bash
# Linux
ls -l /var/log/flask_app
ls -l /var/run/flask_app
ls -l instance/

# Should show proper ownership (usually ec2-user:ec2-user)
```

3. Common issues:

- If the app fails to start:
  ```bash
  # Check if gunicorn is running
  ps aux | grep gunicorn
  
  # Check if port is already in use
  sudo lsof -i :8000
  
  # Restart the service
  sudo systemctl restart flask_app
  ```

- If database migrations fail:
  ```bash
  # Remove existing migrations
  rm -rf migrations/
  
  # Reinitialize migrations
  flask db init
  flask db migrate
  flask db upgrade
  ```

- For detailed debugging:
  ```bash
  # Check service status
  sudo systemctl status flask_app
  
  # Check all logs
  sudo journalctl -u flask_app -f
  
  # Verify file permissions
  ls -la /var/log/flask_app/
  ls -la /var/run/flask_app/
  ls -la instance/
