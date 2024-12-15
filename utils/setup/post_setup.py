"""
Post-setup initialization script for plugins
"""
import os
from flask_migrate import upgrade
from app import create_app, db

def init_aws_regions(app):
    """Initialize default AWS regions"""
    with app.app_context():
        # Import models here to avoid circular imports
        from app.plugins.awsmon.models import AWSRegion
        
        regions = [
            ('US East (N. Virginia)', 'us-east-1'),
            ('US West (Oregon)', 'us-west-2')
        ]
        
        for name, code in regions:
            if not AWSRegion.query.filter_by(code=code).first():
                region = AWSRegion(name=name, code=code)
                db.session.add(region)
        
        try:
            db.session.commit()
            print("Initialized AWS regions")
        except Exception as e:
            print(f"Error initializing AWS regions: {e}")
            db.session.rollback()

def run_post_setup():
    """Run post-setup initialization"""
    print("\nRunning post-setup initialization...")
    
    # Create app without skipping migrations or plugins
    os.environ.pop('SKIP_MIGRATIONS', None)
    os.environ.pop('SKIP_PLUGIN_LOAD', None)
    
    app = create_app()
    
    with app.app_context():
        # Run all migrations
        upgrade()
        print("Database migrations completed")
        
        # Initialize AWS regions
        init_aws_regions(app)
    
    print("\nPost-setup initialization complete!")
    print("\nYou can now access the AWS Monitor plugin at:")
    print("  /awsmon/dashboard - Main monitoring dashboard")
    print("  /awsmon/synthetic - Synthetic monitoring")
    print("  /awsmon/settings - AWS credentials and settings")

if __name__ == '__main__':
    run_post_setup()
