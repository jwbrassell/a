# Setup Guide

## System Requirements

- Python 3.8+
- MariaDB/MySQL
- Git
- Virtual Environment support

## Installation Steps

### 1. Database Setup

```bash
# Install MariaDB if needed
# On macOS:
brew install mariadb
# On Ubuntu:
sudo apt-get install mariadb-server

# Start MariaDB service
# On macOS:
brew services start mariadb
# On Ubuntu:
sudo systemctl start mariadb

# Create database
mysql -u root -p
CREATE DATABASE blackfridaylunch;
CREATE USER 'bflunch'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON blackfridaylunch.* TO 'bflunch'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Application Setup

```bash
# Clone repository
git clone [repository-url]
cd blackfridaylunch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings:
# - Database credentials
# - Secret key
# - LDAP settings
# - Other configuration options

# Initialize database
flask db upgrade
python init_db.py
python init_database_values.py
```

### 3. Plugin Configuration

Each plugin may require additional setup:

#### Documents Plugin
- Configure upload directory in .env
- Ensure proper permissions on upload directory

#### Dispatch Plugin
- Set up required categories
- Configure notification settings

#### Projects Plugin
- Initialize project settings
- Set up role permissions

#### On-call Plugin
- Configure schedule rotation
- Set up notification channels

### 4. Running the Application

Development server:
```bash
flask run
```

Production deployment with gunicorn:
```bash
gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
```

### 5. First-time Setup

1. Create admin user:
```bash
python init_database_values.py --create-admin
```

2. Log in with default credentials:
- Username: admin
- Password: (check .env.example)

3. Change admin password immediately

### 6. Verification

1. Access http://localhost:5000
2. Verify database connectivity
3. Test LDAP authentication
4. Check plugin functionality
5. Verify file uploads
6. Test report generation

## Troubleshooting

### Common Issues

1. Database Connection
```bash
# Check database status
mysql -u bflunch -p blackfridaylunch
# Verify credentials in .env
```

2. LDAP Connection
- Check LDAP server accessibility
- Verify credentials
- Test with mock_ldap if needed

3. File Permissions
```bash
# Fix upload directory permissions
chmod -R 755 app/static/uploads
```

4. Migration Issues
```bash
# Reset migrations
flask db stamp head
flask db migrate
flask db upgrade
```

### Getting Help

- Check logs in logs/ directory
- Review error messages in browser console
- Submit issues with detailed error information
