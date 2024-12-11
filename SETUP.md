# Setup Guide

## Quick Start (Development with SQLite)

1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run setup:
   ```bash
   python setup.py
   ```
4. Start the application:
   ```bash
   flask run
   ```
5. Login with:
   - Username: admin
   - Password: test123

That's it! The setup script automatically:
- Creates the .env file with secure defaults
- Initializes the SQLite database
- Creates all required tables
- Sets up initial data

## Production Setup (MariaDB)

For production environments using MariaDB:

1. Install MariaDB:
   ```bash
   # On Rocky Linux/RHEL/CentOS:
   sudo dnf install mariadb-server
   sudo systemctl enable mariadb
   sudo systemctl start mariadb
   ```

2. Secure the installation:
   ```bash
   sudo mysql_secure_installation
   ```

3. Set root password:
   ```bash
   sudo mysql -u root
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'your-root-password';
   FLUSH PRIVILEGES;
   exit;
   ```

4. Configure environment:
   ```bash
   # Edit .env file (created by setup.py) and update:
   MYSQL_ROOT_PASSWORD=your-root-password
   DATABASE_USER=flask_app_user
   DATABASE_PASSWORD=your-password-here
   DATABASE_HOST=localhost
   DATABASE_NAME=portal_db
   ```

5. Run setup with MariaDB flag:
   ```bash
   python setup.py --mariadb
   ```

## Configuration

The setup script creates a .env file with secure defaults. You can modify these settings:

### Core Settings
```ini
FLASK_APP=app.py
FLASK_ENV=development  # or production
SECRET_KEY=auto-generated-secure-key
```

### Optional Settings
```ini
# Mail Configuration (for Dispatch Plugin)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@example.com
```

## Troubleshooting

### SQLite Issues

1. "unable to open database file":
   - Check instance directory permissions
   - Run setup.py again to recreate the database

2. Database locked:
   - Stop any running flask instances
   - Check for other processes using the database

### MariaDB Issues

1. Access denied for root:
   - Verify MYSQL_ROOT_PASSWORD in .env
   - Ensure MariaDB is running:
     ```bash
     sudo systemctl status mariadb
     ```

2. Connection issues:
   - Check if MariaDB is running
   - Verify DATABASE_HOST setting
   - Test connection:
     ```bash
     mysql -u flask_app_user -p
     ```

## Command Line Options

```bash
python setup.py           # Use SQLite (default)
python setup.py --mariadb # Use MariaDB
python setup.py --help    # Show help
