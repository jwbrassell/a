from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash

# Association Tables
user_role = db.Table('user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

page_route_roles = db.Table('page_route_roles',
    db.Column('page_route_id', db.Integer, db.ForeignKey('page_route_mapping.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    """User model for authentication and user management."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    employee_number = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    cngroup = db.Column(db.String(128), nullable=True)
    vzid = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)

    # Relationships
    roles = db.relationship('Role', secondary=user_role, backref=db.backref('users', lazy=True))
    page_visits = db.relationship('PageVisit', backref='user', lazy=True)

    def __init__(self, username, employee_number, name, email, vzid, roles=None, cngroup=None, password=None):
        self.username = username
        self.employee_number = employee_number
        self.name = name
        self.email = email
        self.vzid = vzid
        self.cngroup = cngroup
        self.roles = roles or []
        if password:
            self.set_password(password)

    def set_password(self, password):
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    def has_role(self, role_name):
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    """Role model for user permissions."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    notes = db.Column(db.String(200), nullable=True)
    icon = db.Column(db.String(64), nullable=False, default='fa-user-shield')
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_by = db.Column(db.String(64), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # Add relationship to PageRouteMapping
    page_routes = db.relationship('PageRouteMapping', secondary=page_route_roles, 
                                backref=db.backref('allowed_roles', lazy=True))

    def __repr__(self):
        return f'<Role {self.name}>'

class NavigationCategory(db.Model):
    """Model for grouping routes in navigation."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    icon = db.Column(db.String(64), nullable=False, default='fa-folder')
    weight = db.Column(db.Integer, nullable=False, default=0)
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_by = db.Column(db.String(64), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationship to route mappings
    routes = db.relationship('PageRouteMapping', backref='nav_category', lazy=True)

    def __repr__(self):
        return f'<NavigationCategory {self.name}>'

class PageRouteMapping(db.Model):
    """Model for mapping routes to roles for RBAC."""
    
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(128), nullable=False)
    route = db.Column(db.String(256), nullable=False, unique=True)
    icon = db.Column(db.String(64), nullable=False, default='fa-link')
    weight = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to navigation category with named constraint
    category_id = db.Column(db.Integer, db.ForeignKey('navigation_category.id', name='fk_page_route_category'),
                           nullable=True)

    def __repr__(self):
        return f'<PageRouteMapping {self.page_name} -> {self.route}>'

class UserActivity(db.Model):
    """UserActivity model for tracking user actions."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    activity = db.Column(db.String(512), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, username, activity):
        self.user_id = user_id
        self.username = username
        self.activity = activity

    def __repr__(self):
        return f'<UserActivity {self.username}: {self.activity}>'

class PageVisit(db.Model):
    """Model for tracking all page visits."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(150), nullable=True)
    route = db.Column(db.String(256), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)

    def __init__(self, route, method, status_code, user_id=None, username=None, ip_address=None, user_agent=None):
        self.route = route
        self.method = method
        self.status_code = status_code
        self.user_id = user_id
        self.username = username
        self.ip_address = ip_address
        self.user_agent = user_agent

    def __repr__(self):
        return f'<PageVisit {self.route} [{self.status_code}] by {self.username or "anonymous"}>'
