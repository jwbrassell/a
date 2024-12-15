"""Navigation-related models."""
from datetime import datetime
from app.extensions import db

# Association table for route roles
route_roles = db.Table('route_roles',
    db.Column('route_id', db.Integer, db.ForeignKey('page_route_mapping.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

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
