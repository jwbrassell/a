import os
import sys
from getpass import getpass
from dotenv import load_dotenv
import pymysql
import subprocess
from pathlib import Path

def prompt_db_info():
    """Prompt user for database connection information"""
    print("\n=== MariaDB Connection Setup ===")
    print("Please provide your MariaDB connection details:\n")
    
    host = input("Database Host [localhost]: ").strip() or "localhost"
    port = input("Database Port [3306]: ").strip() or "3306"
    database = input("Database Name [portal_db]: ").strip() or "portal_db"
    username = input("Database Username: ").strip()
    password = getpass("Database Password: ")
    
    return {
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password
    }

def test_connection(db_info):
    """Test the database connection with provided credentials"""
    print("\nTesting database connection...")
    try:
        connection = pymysql.connect(
            host=db_info["host"],
            port=int(db_info["port"]),
            user=db_info["username"],
            password=db_info["password"]
        )
        connection.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def create_database_if_not_exists(db_info):
    """Create the database if it doesn't exist"""
    try:
        connection = pymysql.connect(
            host=db_info["host"],
            port=int(db_info["port"]),
            user=db_info["username"],
            password=db_info["password"]
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_info['database']}`")
            # Set character set and collation
            cursor.execute(f"ALTER DATABASE `{db_info['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.close()
        print(f"✅ Database '{db_info['database']}' is ready")
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {str(e)}")
        return False

def update_env_file(db_info):
    """Update .env file with MariaDB configuration"""
    print("\nUpdating .env file...")
    
    env_content = f"""# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
WTF_CSRF_ENABLED=True

# Database Configuration
DB_TYPE=mariadb
DATABASE_USER={db_info['username']}
DATABASE_PASSWORD={db_info['password']}
DATABASE_HOST={db_info['host']}
DATABASE_PORT={db_info['port']}
DATABASE_NAME={db_info['database']}

# SQLite Configuration (backup)
SQLITE_PATH=instance/app.db

# Session Configuration
SESSION_TYPE=sqlalchemy
SESSION_SQLALCHEMY_TABLE=sessions
PERMANENT_SESSION_LIFETIME=7200
SESSION_USE_SIGNER=True
SESSION_FILE_THRESHOLD=500

# Plugin Configuration
SKIP_PLUGIN_LOAD=0
SKIP_MIGRATIONS=0

# Mail Configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@example.com

# LDAP Configuration
LDAP_HOST=ldap.example.com
LDAP_PORT=389
LDAP_USE_SSL=False
LDAP_BASE_DN=dc=example,dc=com
LDAP_USER_DN=ou=users
LDAP_GROUP_DN=ou=groups
LDAP_USER_RDN_ATTR=uid
LDAP_USER_LOGIN_ATTR=uid
LDAP_BIND_USER_DN=
LDAP_BIND_USER_PASSWORD=

# Vault Configuration
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your-vault-token-here

# Application Settings
DEBUG=True
TESTING=False
SQLALCHEMY_TRACK_MODIFICATIONS=False
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file updated successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to update .env file: {str(e)}")
        return False

def run_migrations():
    """Run database migrations"""
    print("\nRunning database migrations...")
    try:
        # Clean any existing migrations
        subprocess.run([sys.executable, "-m", "flask", "db", "stamp", "head"], check=True)
        
        # Run Flask-Migrate commands
        subprocess.run([sys.executable, "-m", "flask", "db", "upgrade"], check=True)
        
        print("✅ Database migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check if all required packages are installed")
        print("2. Verify database connection settings")
        print("3. Check if there are any conflicting migrations")
        print("4. Try running with FLASK_DEBUG=1 for more detailed error messages")
        print("5. Ensure MariaDB server is running and accessible")
        return False

def verify_plugins():
    """Verify plugin configurations"""
    print("\nVerifying plugin configurations...")
    try:
        # Set environment variable to load plugins during verification
        os.environ['SKIP_PLUGIN_LOAD'] = '0'
        os.environ['SKIP_MIGRATIONS'] = '1'  # Skip migrations during verification
        
        # Try importing and initializing the app
        from app import create_app
        app = create_app()
        
        with app.app_context():
            print("✅ Plugin configurations verified successfully")
        return True
    except Exception as e:
        print(f"❌ Plugin verification failed: {str(e)}")
        return False

def main():
    print("=== SQLite to MariaDB Migration Tool ===")
    print("This tool will help you migrate your Flask application from SQLite to MariaDB.")
    print("Make sure MariaDB is installed and running before proceeding.\n")
    
    # Load existing .env file if it exists
    load_dotenv()
    
    # Get database information
    db_info = prompt_db_info()
    
    # Test connection
    if not test_connection(db_info):
        print("\n❌ Migration aborted due to connection failure")
        return
    
    # Create database
    if not create_database_if_not_exists(db_info):
        print("\n❌ Migration aborted due to database creation failure")
        return
    
    # Update .env file
    if not update_env_file(db_info):
        print("\n❌ Migration aborted due to .env update failure")
        return
    
    # Verify plugin configurations
    if not verify_plugins():
        print("\n⚠️ Warning: Plugin verification failed, but continuing with migration")
    
    # Run migrations
    if not run_migrations():
        print("\n❌ Migration aborted due to migration failure")
        return
    
    print("\n✅ Migration completed successfully!")
    print("\nYour application is now configured to use MariaDB.")
    print(f"Database: {db_info['database']} on {db_info['host']}:{db_info['port']}")
    print("\nNext steps:")
    print("1. Review and update the .env file with your specific configurations")
    print("2. Test the application thoroughly")
    print("3. If needed, run 'flask db stamp head' to mark all migrations as complete")
    print("4. Consider backing up your SQLite database before removing it")
    print("5. Update your deployment scripts to use MariaDB configuration")

if __name__ == "__main__":
    main()
