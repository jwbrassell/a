"""AWS Monitoring plugin for Flask application."""
from flask import Blueprint
from app.utils.plugin_base import PluginBase, PluginMetadata

class AWSMonitorPlugin(PluginBase):
    """AWS Monitor plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="AWS Monitor",
            version="1.0.0",
            description="AWS infrastructure monitoring and management with EC2 instance tracking, synthetic testing, and jump server management",
            author="System",
            required_roles=["admin", "user"],
            permissions=[
                "awsmon_dashboard_access",
                "awsmon_instances_access",
                "awsmon_synthetic_access",
                "awsmon_templates_access",
                "awsmon_settings_access"
            ],
            icon="fa-cloud",
            category="monitoring",
            weight=50,
            entry_point="/awsmon",
            dashboard_template="awsmon/dashboard.html",
            settings_template="awsmon/settings.html"
        )
        super().__init__(metadata)
        
        self.blueprint = Blueprint(
            'awsmon',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/awsmon/static',
            url_prefix='/awsmon'
        )

    def init_app(self, app):
        """Initialize the AWS monitoring plugin."""
        super().init_app(app)
        
        # Import models to ensure they're registered with SQLAlchemy
        from . import models
        
        # Import route modules
        from . import (
            instance_routes,
            synthetic_routes,
            template_routes
        )
        
        # Initialize plugin
        with app.app_context():
            # Register permissions
            from app.utils.enhanced_rbac import register_permission
            for permission in self.metadata.permissions:
                register_permission(
                    permission,
                    f"Permission for {permission}"
                )

# Create plugin instance
plugin = AWSMonitorPlugin()
