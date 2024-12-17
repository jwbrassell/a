"""User-related models."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, cache_manager

# Association table for user roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
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
    last_login = db.Column(db.DateTime)
    
    # Avatar fields
    avatar_data = db.Column(db.LargeBinary)
    avatar_mimetype = db.Column(db.String(32))
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                          back_populates='users')
    preferences = db.relationship('UserPreference', backref='user', lazy=True,
                                cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def has_role(self, role_name):
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission_name):
        """Check if user has a specific permission through any of their roles."""
        return any(
            any(p.name == permission_name for p in role.get_permissions())
            for role in self.roles
        )

    def get_permissions(self):
        """Get all permissions from all roles."""
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_permissions())
        return list(permissions)

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

    def set_avatar(self, image_data, mimetype):
        """Set user avatar."""
        self.avatar_data = image_data
        self.avatar_mimetype = mimetype
        # Clear the cached avatar
        cache_manager.memory_cache.delete(f'avatar_{self.id}')

    def get_avatar_url(self):
        """Get URL for avatar image."""
        if self.avatar_data:
            # Return URL to avatar endpoint
            return f'/profile/avatar/{self.id}'
        # Return URL to default avatar
        return '/static/images/user_1.jpg'

    def get_avatar_data(self):
        """Get avatar data with caching."""
        if not self.avatar_data:
            return None, None

        # Try to get from cache first
        cached_data = cache_manager.memory_cache.get(f'avatar_{self.id}')
        if cached_data:
            return cached_data, self.avatar_mimetype

        # If not in cache, get from database and cache it
        cache_manager.memory_cache.set(f'avatar_{self.id}', self.avatar_data, timeout=3600)  # Cache for 1 hour
        return self.avatar_data, self.avatar_mimetype

    def __repr__(self):
        return f'<User {self.username}>'

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
