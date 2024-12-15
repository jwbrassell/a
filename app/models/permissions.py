"""Association tables for RBAC relationships."""
from app.extensions import db
from datetime import datetime

# Association tables
permission_actions = db.Table('permission_actions',
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
    db.Column('action_id', db.Integer, db.ForeignKey('action.id'), primary_key=True)
)

role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class Action(db.Model):
    """Action model for HTTP method-based permissions."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # e.g., 'read', 'write', 'delete'
    method = db.Column(db.String(10))  # HTTP method
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(64), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('name', 'method', name='_action_method_uc'),)

    def __repr__(self):
        return f'<Action {self.name} ({self.method})>'

class RoutePermission(db.Model):
    """Route to Permission mapping."""
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(256), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(64), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('route', 'permission_id', name='_route_permission_uc'),)

    def __repr__(self):
        return f'<RoutePermission {self.route}>'
