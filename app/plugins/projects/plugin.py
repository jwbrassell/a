"""Projects plugin initialization and configuration."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()

def route_to_endpoint(route: str) -> str:
    """Convert route name to endpoint name.
    For example: 'index' -> 'projects.index'
             'dashboard' -> 'projects.project_dashboard'
    """
    if not route:
        return ''
    
    # If it's already a fully qualified endpoint (contains a dot), return as is
    if '.' in route:
        return route
        
    # Map common route names to their endpoints
    route_map = {
        'index': 'projects.index',
        'dashboard': 'projects.project_dashboard',
        'kanban': 'projects.project_kanban',
        'calendar': 'projects.project_calendar',
        'timeline': 'projects.project_timeline',
        'settings': 'projects.project_settings',
        'reports': 'projects.project_reports',
        'list': 'projects.list_projects',
        'new': 'projects.new_project',
        'create': 'projects.create_project'
    }
    
    # Return mapped endpoint or default to projects.{route}
    return route_map.get(route, f'projects.{route}')

def init_plugin(app: Flask) -> None:
    """Initialize the projects plugin"""
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/projects.log',
            maxBytes=1024 * 1024,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Projects plugin startup')
    
    # Register Jinja2 filters
    app.jinja_env.filters['route_to_endpoint'] = route_to_endpoint
    
    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize caching
    from .utils.caching import init_cache
    init_cache(app)
    
    # Initialize monitoring if enabled
    if app.config.get('ENABLE_QUERY_TRACKING'):
        from .utils.monitoring import init_monitoring
        init_monitoring(app)
    
    # Register CLI commands
    register_commands(app)

def register_commands(app: Flask) -> None:
    """Register CLI commands"""
    
    @app.cli.group()
    def projects():
        """Projects plugin commands"""
        pass
    
    @projects.command()
    def init_db():
        """Initialize database tables"""
        db.create_all()
        print('Initialized database.')
    
    @projects.command()
    def clear_cache():
        """Clear all cache entries"""
        from .utils.caching import cache
        cache.clear()
        print('Cache cleared.')
    
    @projects.command()
    def performance_report():
        """Generate performance report"""
        from .utils.monitoring import get_performance_report
        report = get_performance_report()
        print(report)

# Version information
__version__ = '1.0.0'
