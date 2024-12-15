"""Role model with enhanced RBAC support."""
from app.extensions import db
from datetime import datetime
from typing import Dict, Any, List
from app.models.permissions import role_permissions

class Role(db.Model):
    """Role model with hierarchy support and permission relationships."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    notes = db.Column(db.Text)  # Longer notes/documentation about the role
    icon = db.Column(db.String(50), default='fas fa-user-tag')  # FontAwesome icon class
    is_system_role = db.Column(db.Boolean, default=False)  # System roles cannot be deleted
    weight = db.Column(db.Integer, default=0)  # For ordering in UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(64), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(64))
    
    # Role hierarchy
    parent_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    parent = db.relationship('Role', remote_side=[id], backref='children')
    
    # Relationships
    users = db.relationship('User', secondary='user_roles', back_populates='roles')
    permissions = db.relationship(
        'Permission',
        secondary=role_permissions,
        back_populates='roles',
        overlaps="roles"
    )
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'notes': self.notes,
            'icon': self.icon,
            'is_system_role': self.is_system_role,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by,
            'parent_id': self.parent_id,
            'user_count': len(self.users),
            'permission_count': len(self.permissions),
            'children': [child.id for child in self.children]
        }
    
    def get_permissions(self, include_parent=True) -> List['Permission']:
        """Get all permissions for this role, optionally including parent permissions."""
        all_permissions = set(self.permissions)
        
        if include_parent and self.parent:
            all_permissions.update(self.parent.get_permissions())
        
        return list(all_permissions)
    
    def has_permission(self, permission: str, include_parent=True) -> bool:
        """Check if role has a specific permission."""
        # Check direct permissions
        if any(p.name == permission for p in self.permissions):
            return True
            
        # Check parent permissions if requested
        if include_parent and self.parent:
            return self.parent.has_permission(permission)
            
        return False
    
    def add_permission(self, permission: 'Permission') -> None:
        """Add a permission to this role if it doesn't already have it."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: 'Permission') -> None:
        """Remove a permission from this role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def get_hierarchy_level(self) -> int:
        """Get the level of this role in the hierarchy (0 is top level)."""
        level = 0
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level
    
    def is_ancestor_of(self, role: 'Role') -> bool:
        """Check if this role is an ancestor of the given role."""
        current = role
        while current.parent:
            if current.parent == self:
                return True
            current = current.parent
        return False
    
    def is_descendant_of(self, role: 'Role') -> bool:
        """Check if this role is a descendant of the given role."""
        return role.is_ancestor_of(self)
    
    def get_ancestors(self) -> List['Role']:
        """Get all ancestor roles."""
        ancestors = []
        current = self
        while current.parent:
            ancestors.append(current.parent)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> List['Role']:
        """Get all descendant roles."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    @staticmethod
    def get_role_tree() -> List[Dict[str, Any]]:
        """Get the complete role hierarchy as a tree structure."""
        def build_tree(role: 'Role') -> Dict[str, Any]:
            return {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'icon': role.icon,
                'is_system_role': role.is_system_role,
                'user_count': len(role.users),
                'permission_count': len(role.permissions),
                'children': [build_tree(child) for child in role.children]
            }
        
        # Get all top-level roles (roles without parents)
        root_roles = Role.query.filter_by(parent_id=None).all()
        return [build_tree(role) for role in root_roles]

    @staticmethod
    def get_available_permissions() -> List[Dict[str, Any]]:
        """Get all available permissions grouped by category."""
        from app.models import Permission
        permissions = Permission.query.all()
        
        # Group permissions by category
        grouped = {}
        for perm in permissions:
            category = perm.name.split('_')[0]  # Use first part of name as category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                'id': perm.id,
                'name': perm.name,
                'description': perm.description
            })
        
        return grouped

    def can_be_deleted(self) -> bool:
        """Check if role can be safely deleted."""
        # System roles cannot be deleted
        if self.is_system_role:
            return False
        
        # Roles with users cannot be deleted
        if self.users:
            return False
        
        # Roles with children cannot be deleted
        if self.children:
            return False
        
        return True

    def get_user_count(self) -> int:
        """Get number of users with this role."""
        return len(self.users)

    def get_effective_permissions(self) -> List['Permission']:
        """Get all effective permissions including inherited ones."""
        return self.get_permissions(include_parent=True)
