"""Role model with enhanced RBAC support."""
from app.extensions import db
from datetime import datetime

class Role(db.Model):
    """Role model with hierarchy support and permission relationships."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(64), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Role hierarchy
    parent_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    parent = db.relationship('Role', remote_side=[id], backref='children')
    
    # User relationship (existing)
    users = db.relationship('User', secondary='user_roles', back_populates='roles')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def get_permissions(self, include_parent=True):
        """Get all permissions for this role, optionally including parent permissions."""
        all_permissions = set(self.permissions)
        
        if include_parent and self.parent:
            all_permissions.update(self.parent.get_permissions())
        
        return list(all_permissions)
    
    def has_permission(self, permission, include_parent=True):
        """Check if role has a specific permission."""
        if permission in self.permissions:
            return True
            
        if include_parent and self.parent:
            return self.parent.has_permission(permission)
            
        return False
    
    def add_permission(self, permission):
        """Add a permission to this role if it doesn't already have it."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission):
        """Remove a permission from this role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def get_hierarchy_level(self):
        """Get the level of this role in the hierarchy (0 is top level)."""
        level = 0
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level
    
    def is_ancestor_of(self, role):
        """Check if this role is an ancestor of the given role."""
        current = role
        while current.parent:
            if current.parent == self:
                return True
            current = current.parent
        return False
    
    def is_descendant_of(self, role):
        """Check if this role is a descendant of the given role."""
        return role.is_ancestor_of(self)
    
    def get_ancestors(self):
        """Get all ancestor roles."""
        ancestors = []
        current = self
        while current.parent:
            ancestors.append(current.parent)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        """Get all descendant roles."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    @staticmethod
    def get_role_tree():
        """Get the complete role hierarchy as a tree structure."""
        def build_tree(role):
            return {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'children': [build_tree(child) for child in role.children]
            }
        
        # Get all top-level roles (roles without parents)
        root_roles = Role.query.filter_by(parent_id=None).all()
        return [build_tree(role) for role in root_roles]
