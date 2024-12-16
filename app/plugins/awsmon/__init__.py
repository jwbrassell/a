"""
AWS Monitor Plugin

Plugin for monitoring AWS resources and services.
"""

from flask import Blueprint, render_template, jsonify, request
from app.utils.plugin_base import PluginBase, PluginMetadata
from flask_login import login_required
from app.utils.enhanced_rbac import requires_permission, register_permission
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
import logging

# Configure logging
logger = logging.getLogger(__name__)

class AWSMonitorPlugin(PluginBase):
    """AWS Monitor plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name='awsmon',
            version='1.0.0',
            description='Monitor AWS resources and services',
            author='Admin',
            required_roles=['admin', 'devops'],
            icon='fas fa-cloud',
            category='monitoring',
            weight=50
        )
        super().__init__(metadata)
        
        # Create blueprint with standard configuration
        self.blueprint = Blueprint(
            'awsmon',
            __name__,
            template_folder='templates',
            static_folder='static',
            url_prefix='/awsmon'
        )
        
        # Register main routes
        self.register_main_routes()
        
        # Register feature routes
        self.register_routes()
        
        # Register models
        self.register_models()
        
        # Register CLI commands
        self.register_commands()
        
        # Register template filters
        self.register_template_filters()
        
        # Register context processors
        self.register_context_processors()

    def init_app(self, app):
        """Initialize plugin with Flask application."""
        super().init_app(app)
        
        # Register permissions
        with app.app_context():
            # Register base permissions
            register_permission('awsmon_access', 'Access AWS Monitor')
            
            # Instance management permissions
            register_permission('awsmon_instances_access', 'Access EC2 instances')
            register_permission('awsmon_instances_manage', 'Manage EC2 instances')
            
            # Synthetic test permissions
            register_permission('awsmon_synthetic_access', 'Access synthetic tests')
            register_permission('awsmon_synthetic_manage', 'Manage synthetic tests')
            
            # Template permissions
            register_permission('awsmon_templates_access', 'Access jump server templates')
            register_permission('awsmon_templates_manage', 'Manage jump server templates')
            
            # Dashboard permissions
            register_permission('awsmon_dashboard_access', 'Access AWS Monitor dashboard')
            
            # Assign permissions to roles
            from app.models import Role, Permission
            admin_role = Role.query.filter_by(name='admin').first()
            devops_role = Role.query.filter_by(name='devops').first()
            
            permissions = [
                'awsmon_access',
                'awsmon_instances_access',
                'awsmon_instances_manage',
                'awsmon_synthetic_access',
                'awsmon_synthetic_manage',
                'awsmon_templates_access',
                'awsmon_templates_manage',
                'awsmon_dashboard_access'
            ]
            
            if admin_role:
                for perm_name in permissions:
                    perm = Permission.query.filter_by(name=perm_name).first()
                    if perm:
                        admin_role.add_permission(perm)
            
            if devops_role:
                for perm_name in permissions:
                    perm = Permission.query.filter_by(name=perm_name).first()
                    if perm:
                        devops_role.add_permission(perm)

            db.session.commit()

            # Register the blueprint with the app
            app.register_blueprint(self.blueprint)

    def register_main_routes(self):
        """Register main plugin routes."""
        if not self.blueprint:
            raise RuntimeError("Blueprint not initialized")

        @self.blueprint.route('/')
        @login_required
        @requires_permission('awsmon_dashboard_access')
        def index():
            """Main AWS Monitor dashboard."""
            try:
                from .models import EC2Instance, SyntheticTest, JumpServerTemplate
                
                # Get counts
                instance_count = EC2Instance.query.filter_by(deleted_at=None).count()
                synthetic_count = SyntheticTest.query.filter_by(deleted_at=None).count()
                template_count = JumpServerTemplate.query.filter_by(deleted_at=None).count()
                
                return render_template('index.html',
                                    instance_count=instance_count,
                                    synthetic_count=synthetic_count,
                                    template_count=template_count)
            except Exception as e:
                logger.error(f"Error in AWS Monitor dashboard: {str(e)}")
                raise

    def register_routes(self):
        """Register plugin routes."""
        if not self.blueprint:
            raise RuntimeError("Blueprint not initialized")

        # Import route modules
        from . import instance_routes, synthetic_routes, template_routes
        
        # Register routes from each module
        instance_routes.register_routes(self.blueprint)
        synthetic_routes.register_routes(self.blueprint)
        template_routes.register_routes(self.blueprint)

    def register_models(self):
        """Register plugin models."""
        try:
            from .models import init_models
            init_models()
            logger.info(f"Registered models for plugin: {self.metadata.name}")
        except ImportError:
            logger.info(f"No models to register for plugin: {self.metadata.name}")
        except Exception as e:
            logger.error(f"Error registering models: {e}")

    def register_commands(self):
        """Register plugin CLI commands."""
        if not self.blueprint:
            return

        @self.blueprint.cli.group()
        def awsmon():
            """AWS Monitor plugin commands."""
            pass

        @awsmon.command()
        def sync():
            """Sync AWS resources."""
            try:
                # Add sync logic here
                logger.info("Synced AWS resources")
            except Exception as e:
                logger.error(f"Error syncing AWS resources: {e}")
                raise

    def register_template_filters(self):
        """Register plugin template filters."""
        if not self.blueprint:
            return

        @self.blueprint.app_template_filter()
        def instance_status_class(status):
            """Convert instance status to CSS class."""
            status_classes = {
                'running': 'success',
                'stopped': 'warning',
                'terminated': 'danger'
            }
            return status_classes.get(status.lower(), 'secondary')

    def register_context_processors(self):
        """Register plugin context processors."""
        if not self.blueprint:
            return

        @self.blueprint.context_processor
        def inject_aws_regions():
            """Inject AWS regions into template context."""
            from .models import AWSRegion
            regions = AWSRegion.query.filter_by(enabled=True).all()
            return {
                'aws_regions': regions
            }

# Create plugin instance
plugin = AWSMonitorPlugin()

# Make the blueprint available for import
bp = plugin.blueprint
