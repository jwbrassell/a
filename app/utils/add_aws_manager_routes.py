from flask import current_app
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
import importlib

def check_dependencies():
    """Check required dependencies for AWS manager"""
    required_packages = ['boto3', 'botocore']
    missing = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    
    return missing

def init_database():
    """Initialize database tables for AWS manager"""
    try:
        # Import models to ensure they're registered with SQLAlchemy
        from app.blueprints.aws_manager.models import AWSConfiguration, EC2Template
        
        # Create tables if they don't exist
        db.create_all()
        return True
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database initialization error: {str(e)}")
        return False

def add_aws_manager_routes():
    """Add AWS manager routes to the application"""
    try:
        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            current_app.logger.error(f"Missing required packages: {', '.join(missing_deps)}")
            return False

        # Check required configuration
        required_config = ['VAULT_ADDR', 'VAULT_TOKEN']
        missing_config = [key for key in required_config if not current_app.config.get(key)]
        if missing_config:
            current_app.logger.error(f"Missing required configuration: {', '.join(missing_config)}")
            return False

        # Initialize database
        if not init_database():
            current_app.logger.error("Failed to initialize database tables")
            return False

        # Import and initialize the AWS manager blueprint
        from app.blueprints.aws_manager import init_app as init_aws_manager
        
        # Initialize the blueprint
        if init_aws_manager(current_app):
            current_app.logger.info("AWS manager blueprint initialized successfully")
            
            # Log available routes
            routes = []
            for rule in current_app.url_map.iter_rules():
                if rule.endpoint.startswith('aws_manager.'):
                    routes.append(f"{rule.endpoint}: {rule.rule}")
            current_app.logger.info("Registered AWS manager routes:\n" + "\n".join(routes))
            
            return True
        else:
            current_app.logger.warning("Failed to initialize AWS manager blueprint")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error initializing AWS manager blueprint: {str(e)}")
        if current_app.debug:
            import traceback
            current_app.logger.error(traceback.format_exc())
        return False
