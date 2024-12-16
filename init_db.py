"""Initialize database and create tables."""

import eventlet
eventlet.monkey_patch()

from app import create_app
from app.extensions import db
from app.models.metrics import Metric, MetricAlert, MetricDashboard

def init_db():
    """Initialize database and create all tables."""
    app, _ = create_app('development')  # Unpack tuple, ignore socketio
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
