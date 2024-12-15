"""
Base plugin setup functionality
"""
from abc import ABC, abstractmethod
from app import db
from app.models import Role, PageRouteMapping, NavigationCategory

class PluginSetup(ABC):
    """Abstract base class for plugin setup"""
    
    def __init__(self):
        # Don't query roles/categories in __init__ since they may not exist yet
        self.admin_role = None
        self.user_role = None
        self.main_category = None
        self.admin_category = None
    
    def _init_references(self):
        """Initialize role and category references"""
        if not self.admin_role:
            self.admin_role = Role.query.filter_by(name='admin').first()
        if not self.user_role:
            self.user_role = Role.query.filter_by(name='user').first()
        if not self.main_category:
            self.main_category = NavigationCategory.query.filter_by(name='main').first()
        if not self.admin_category:
            self.admin_category = NavigationCategory.query.filter_by(name='admin').first()
        
        if not all([self.admin_role, self.user_role, self.main_category, self.admin_category]):
            raise Exception("Required core data not found. Ensure core data is initialized first.")
    
    @abstractmethod
    def init_data(self):
        """Initialize plugin data - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def init_navigation(self):
        """Initialize plugin navigation - must be implemented by subclasses"""
        pass
    
    def setup(self):
        """Run complete plugin setup"""
        try:
            print(f"\nInitializing {self.__class__.__name__}...")
            # Initialize references before plugin setup
            self._init_references()
            # Initialize plugin data and navigation
            self.init_data()
            self.init_navigation()
            db.session.commit()
            print(f"{self.__class__.__name__} initialization complete")
        except Exception as e:
            print(f"Error initializing {self.__class__.__name__}: {e}")
            db.session.rollback()
            raise
    
    def add_route(self, page_name, route, icon, category_id, weight=0, roles=None):
        """Helper method to add a route to navigation"""
        existing = PageRouteMapping.query.filter_by(route=route).first()
        if not existing:
            route_mapping = PageRouteMapping(
                page_name=page_name,
                route=route,
                icon=icon,
                category_id=category_id,
                weight=weight,
                created_by='system'
            )
            if roles:
                role_objects = Role.query.filter(Role.name.in_(roles)).all()
                route_mapping.allowed_roles.extend(role_objects)
            db.session.add(route_mapping)
            return route_mapping
        return existing

class PluginManager:
    """Manages plugin setup and initialization"""
    
    @staticmethod
    def init_all_plugins():
        """Initialize all plugin data"""
        # Import plugins here to avoid circular dependencies
        plugins = []
        
        try:
            from utils.setup.plugins.projects import ProjectsSetup
            plugins.append(ProjectsSetup())
        except Exception as e:
            print(f"Warning: Failed to load Projects plugin: {e}")
        
        try:
            from utils.setup.plugins.reports import ReportsSetup
            plugins.append(ReportsSetup())
        except Exception as e:
            print(f"Warning: Failed to load Reports plugin: {e}")
        
        try:
            from utils.setup.plugins.awsmon import AwsmonSetup
            plugins.append(AwsmonSetup())
        except Exception as e:
            print(f"Warning: Failed to load AWS Monitor plugin: {e}")
        
        # Add other plugins here as they are implemented
        # try:
        #     from utils.setup.plugins.dispatch import DispatchSetup
        #     plugins.append(DispatchSetup())
        # except Exception as e:
        #     print(f"Warning: Failed to load Dispatch plugin: {e}")
        
        for plugin in plugins:
            try:
                plugin.setup()
            except Exception as e:
                print(f"Warning: Failed to initialize {plugin.__class__.__name__}: {e}")
                print("Continuing with remaining plugins...")
