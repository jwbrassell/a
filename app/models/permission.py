"""Permission model for RBAC system."""

from app.extensions import db
from datetime import datetime
from typing import Dict, Any, List
from app.models.permissions import role_permissions

class Permission(db.Model):
    """Permission model defining granular access controls."""
    
    __tablename__ = 'permission'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256))
    category = db.Column(db.String(64))  # For grouping permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(64), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(64))
    
    # Relationships
    roles = db.relationship(
        'Role',
        secondary=role_permissions,
        back_populates='permissions',
        overlaps="permissions"
    )
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert permission to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by,
            'role_count': self.roles.count()
        }
    
    @staticmethod
    def get_by_name(name: str) -> 'Permission':
        """Get permission by name."""
        return Permission.query.filter_by(name=name).first()
    
    @staticmethod
    def get_by_category(category: str) -> List['Permission']:
        """Get all permissions in a category."""
        return Permission.query.filter_by(category=category).all()
    
    @staticmethod
    def get_categories() -> List[str]:
        """Get list of all permission categories."""
        return [r[0] for r in Permission.query.with_entities(
            Permission.category).distinct().all()]
    
    @staticmethod
    def get_grouped_permissions() -> Dict[str, List['Permission']]:
        """Get all permissions grouped by category."""
        permissions = Permission.query.order_by(
            Permission.category, Permission.name).all()
        grouped = {}
        for perm in permissions:
            if perm.category not in grouped:
                grouped[perm.category] = []
            grouped[perm.category].append(perm)
        return grouped
    
    @staticmethod
    def create_permission(name: str, description: str = None, 
                         category: str = None, created_by: str = 'system') -> 'Permission':
        """Create a new permission."""
        permission = Permission(
            name=name,
            description=description,
            category=category or name.split('_')[0],
            created_by=created_by
        )
        db.session.add(permission)
        db.session.commit()
        return permission
    
    def update(self, **kwargs) -> None:
        """Update permission attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def delete(self) -> None:
        """Delete permission."""
        db.session.delete(self)
        db.session.commit()
    
    def get_roles(self) -> List['Role']:
        """Get all roles that have this permission."""
        return self.roles.all()
    
    def is_used(self) -> bool:
        """Check if permission is used by any roles."""
        return bool(self.roles.count())
    
    @staticmethod
    def initialize_default_permissions():
        """Initialize default system permissions."""
        default_permissions = [
            # Admin permissions
            ('admin_dashboard_access', 'Access admin dashboard', 'admin'),
            ('admin_users_access', 'Access user management', 'admin'),
            ('admin_roles_access', 'Access role management', 'admin'),
            ('admin_monitoring_access', 'Access system monitoring', 'admin'),
            ('admin_logs_access', 'Access system logs', 'admin'),
            
            # User permissions
            ('user_profile_access', 'Access user profile', 'user'),
            ('user_settings_access', 'Access user settings', 'user'),
            
            # Content permissions
            ('content_create', 'Create content', 'content'),
            ('content_edit', 'Edit content', 'content'),
            ('content_delete', 'Delete content', 'content'),
            ('content_publish', 'Publish content', 'content'),
            
            # System permissions
            ('system_settings_access', 'Access system settings', 'system'),
            ('system_backup_access', 'Access backup functionality', 'system'),
            ('system_update_access', 'Access system updates', 'system')
        ]
        
        for name, description, category in default_permissions:
            if not Permission.get_by_name(name):
                Permission.create_permission(
                    name=name,
                    description=description,
                    category=category
                )
