from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from sqlalchemy.dialects.mysql import LONGTEXT

# Association table for user roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# Association table for route roles
route_roles = db.Table('route_roles',
    db.Column('route_id', db.Integer, db.ForeignKey('page_route_mapping.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    employee_number = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    vzid = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                          backref=db.backref('users', lazy=True))
    preferences = db.relationship('UserPreference', backref='user', lazy=True,
                                cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def get_preference(self, key, default=None):
        """Get user preference by key."""
        pref = UserPreference.query.filter_by(user_id=self.id, key=key).first()
        return pref.value if pref else default

    def set_preference(self, key, value):
        """Set user preference."""
        pref = UserPreference.query.filter_by(user_id=self.id, key=key).first()
        if pref:
            pref.value = value
        else:
            pref = UserPreference(user_id=self.id, key=key, value=value)
            db.session.add(pref)

    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    """Role model for user permissions."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    notes = db.Column(db.String(256))
    icon = db.Column(db.String(32))
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(64))
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Role {self.name}>'

class NavigationCategory(db.Model):
    """Model for organizing navigation items."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    icon = db.Column(db.String(32))
    description = db.Column(db.String(256))
    weight = db.Column(db.Integer, default=0)  # For ordering
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(64))
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    routes = db.relationship('PageRouteMapping', backref='category', lazy=True)

    def __repr__(self):
        return f'<NavigationCategory {self.name}>'

class PageRouteMapping(db.Model):
    """Model for mapping pages to routes and managing navigation."""
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(128), nullable=False)
    route = db.Column(db.String(256), unique=True, nullable=False)
    icon = db.Column(db.String(32))
    weight = db.Column(db.Integer, default=0)  # For ordering within category
    category_id = db.Column(db.Integer, db.ForeignKey('navigation_category.id'))
    show_in_navbar = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(64))
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    allowed_roles = db.relationship('Role', secondary=route_roles, lazy='subquery',
                                  backref=db.backref('routes', lazy=True))

    def __repr__(self):
        return f'<PageRouteMapping {self.page_name} -> {self.route}>'

class UserPreference(db.Model):
    """Model for storing user preferences."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    key = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'key', name='_user_key_uc'),)

    def __repr__(self):
        return f'<UserPreference {self.user_id}:{self.key}={self.value}>'

class UserActivity(db.Model):
    """Model for tracking user activities."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))
    activity = db.Column(db.String(512), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserActivity {self.username}: {self.activity}>'

class PageVisit(db.Model):
    """Model for tracking page visits."""
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(256), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PageVisit {self.route}>'

# Let Flask-Session handle the session table
# Remove our Session model definition since Flask-Session will create and manage it

@login_manager.user_loader
def load_user(id):
    """Load user by ID."""
    return User.query.get(int(id))
