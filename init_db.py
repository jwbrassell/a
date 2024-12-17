"""Initialize database tables."""

from app import create_app, db
from app.models.metrics import init_metrics_models

def init_db():
    """Initialize database tables."""
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize metrics models specifically
        init_metrics_models()
        
        print("Database tables created successfully.")

if __name__ == '__main__':
    init_db()
