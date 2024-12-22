from flask import current_app
from app.blueprints.database_reports.plugin import init_app as init_database_reports

def add_database_report_routes():
    """Initialize database reports blueprint"""
    try:
        init_database_reports(current_app)
        current_app.logger.info("Database reports blueprint initialized successfully")
        return True
    except Exception as e:
        current_app.logger.error(f"Error initializing database reports blueprint: {e}")
        return False
