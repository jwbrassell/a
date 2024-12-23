from flask import current_app
from app.blueprints.bug_reports.plugin import init_app as init_bug_reports

def add_bug_report_routes():
    """Initialize bug reports blueprint."""
    try:
        init_bug_reports(current_app)
        return True
    except Exception as e:
        current_app.logger.error(f"Error initializing bug reports blueprint: {e}")
        return False
