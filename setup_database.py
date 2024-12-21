from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.blueprints.aws_manager.models import AWSConfiguration, EC2Template
from app.utils.init_db import init_database
from vault_utility import VaultUtility
import sys

def cleanup_aws_vault():
    """Clean up AWS credentials from vault"""
    try:
        print("Cleaning up AWS credentials from vault...")
        vault = VaultUtility()
        # List and delete all AWS secrets
        aws_paths = vault.list_secrets('aws/')
        if aws_paths:
            for path in aws_paths:
                vault.delete_secret(f"aws/{path}")
        print("AWS vault cleanup completed")
        return True
    except Exception as e:
        print(f"Error cleaning up AWS vault: {e}", file=sys.stderr)
        return False

def setup_database():
    """Set up the database with all required tables and initial data"""
    try:
        app = create_app()
        with app.app_context():
            print("Starting database setup...")
            
            # Clean up AWS credentials from vault
            if not cleanup_aws_vault():
                print("Warning: Failed to clean up AWS vault", file=sys.stderr)
            
            print("Dropping existing tables...")
            db.drop_all()
            
            print("Creating new tables...")
            db.create_all()
            
            print("Initializing database with required data...")
            if not init_database():
                raise Exception("Failed to initialize database with required data")
            
            # Verify AWS manager tables
            print("Verifying AWS manager tables...")
            tables = [
                AWSConfiguration.__table__.name,
                EC2Template.__table__.name
            ]
            existing_tables = db.engine.table_names()
            missing_tables = [t for t in tables if t not in existing_tables]
            if missing_tables:
                raise Exception(f"Missing AWS manager tables: {', '.join(missing_tables)}")
            
            print("Database setup completed successfully")
            return True
            
    except Exception as e:
        print(f"Error setting up database: {e}", file=sys.stderr)
        if app.debug:
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
        return False

def main():
    """Main entry point with error handling"""
    try:
        if setup_database():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
