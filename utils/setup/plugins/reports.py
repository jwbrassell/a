"""
Reports plugin setup module
"""
from app.extensions import db
from app.plugins.reports.models import DatabaseConnection, ReportView
from utils.setup.plugin_setup import PluginSetup

class ReportsSetup(PluginSetup):
    """Handle reports plugin initialization"""
    
    def init_data(self):
        """Initialize reports data"""
        admin = db.session.query(db.models.User).filter_by(username='admin').first()
        
        # Initialize default database connections
        connections = [
            {
                'name': 'Application DB',
                'description': 'Main application database',
                'db_type': 'sqlite',
                'database': 'instance/app.db',
                'created_by': admin.id,
                'username': None,  # SQLite doesn't need credentials
            }
        ]
        
        for conn_data in connections:
            conn = db.session.query(DatabaseConnection).filter_by(name=conn_data['name']).first()
            if not conn:
                # Create database connection without credentials
                conn = DatabaseConnection(
                    name=conn_data['name'],
                    description=conn_data['description'],
                    db_type=conn_data['db_type'],
                    database=conn_data['database'],
                    username=conn_data['username'],
                    created_by=conn_data['created_by']
                )
                db.session.add(conn)
                db.session.flush()  # Flush to get the ID
                
                # Try to store empty credentials in vault
                try:
                    from app.plugins.reports.vault_utils import vault_manager
                    vault_manager.store_database_credentials(
                        conn.id,
                        {'password': None}  # SQLite doesn't need credentials
                    )
                except Exception as e:
                    print(f"Warning: Failed to store credentials in vault: {e}")
                    print("You may need to manually add credentials later")
        
        db.session.commit()
        
        # Initialize default report views
        app_db = db.session.query(DatabaseConnection).filter_by(name='Application DB').first()
        
        views = [
            {
                'title': 'Active Users',
                'description': 'List of all active users in the system',
                'database_id': app_db.id,
                'query': 'SELECT username, name, email FROM user WHERE is_active = 1',
                'column_config': {
                    'username': {'label': 'Username'},
                    'name': {'label': 'Full Name'},
                    'email': {'label': 'Email Address'}
                },
                'is_private': False,
                'created_by': admin.id
            }
        ]
        
        for view_data in views:
            view = db.session.query(ReportView).filter_by(title=view_data['title']).first()
            if not view:
                view = ReportView(**view_data)
                db.session.add(view)
    
    def init_navigation(self):
        """Initialize reports navigation"""
        # Add reports section to main navigation
        self.add_route(
            page_name='Reports',
            route='/reports',
            icon='fa-chart-bar',
            category_id=self.main_category.id,
            weight=50,
            roles=['user']  # Available to all users
        )
        
        # Add reports admin section
        self.add_route(
            page_name='Reports Admin',
            route='/reports/admin',
            icon='fa-database',
            category_id=self.admin_category.id,
            weight=50,
            roles=['admin']  # Admin only
        )
